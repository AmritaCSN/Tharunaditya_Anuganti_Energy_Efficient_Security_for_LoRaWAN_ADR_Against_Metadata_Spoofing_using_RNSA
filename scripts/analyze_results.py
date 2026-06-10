"""
analyze_results.py - Full experiment matrix analysis for LoRaWAN ADR-Secure paper.

Usage:
    python scripts/analyze_results.py             # analyse existing CSVs
    python scripts/analyze_results.py --no-plots  # tables only, skip matplotlib
    python scripts/analyze_results.py --export    # export all pending SCA files then analyse

Outputs (to results/figures/ and results/tables/):
    fig1_sf_distribution.pdf/png
    fig2_pdr_vs_K.pdf/png
    fig3_energy_vs_K.pdf/png
    fig4_sf_mean_vs_K.pdf/png
    fig5_collisions_vs_K.pdf/png
    table1_summary.tex
    table2_sf_distribution.tex
    summary_console.txt

Requires: matplotlib, numpy  (pip install matplotlib numpy)
"""

# Force UTF-8 output on Windows to avoid cp1252 encode errors
import sys, io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import csv, os, statistics, subprocess, traceback as _tb

# Global exception hook — saves traceback to error.log and prints it clearly
_RESULTS_DIR_EARLY = r"C:\omnet-workspace\results"
def _exc_hook(etype, value, tb):
    msg = "".join(_tb.format_exception(etype, value, tb))
    print(f"\n{'='*60}\n[FATAL ERROR] {etype.__name__}: {value}\n{'='*60}\n{msg}", file=sys.stderr)
    try:
        os.makedirs(_RESULTS_DIR_EARLY, exist_ok=True)
        with open(os.path.join(_RESULTS_DIR_EARLY, "analyze_error.log"), "w", encoding="utf-8") as _f:
            _f.write(msg)
        print(f"[FATAL] Full traceback saved to {_RESULTS_DIR_EARLY}\\analyze_error.log", file=sys.stderr)
    except Exception:
        pass
    sys.exit(1)
sys.excepthook = _exc_hook

# ── Detect matplotlib ──────────────────────────────────────────────────────────
_PLOTS = True
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
except ImportError:
    _PLOTS = False
    print("[WARN] matplotlib/numpy not installed - plots skipped.")
    print("       Run: pip install matplotlib numpy")

# ── Paths ──────────────────────────────────────────────────────────────────────
RESULTS_DIR = r"C:\omnet-workspace\results"
SCA_DIR     = r"C:\omnet-workspace\flora\simulations\results"
FIG_DIR     = os.path.join(RESULTS_DIR, "figures")
TAB_DIR     = os.path.join(RESULTS_DIR, "tables")
BASH        = r"C:\omnetpp\tools\win32.x86_64\usr\bin\bash.exe"
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TAB_DIR, exist_ok=True)

# ── Scenario registry ──────────────────────────────────────────────────────────
# (csv_filename, label, stype, K, adr_mode, gw_count, offset_dB)
SCENARIOS = [
    ("week1_baseline_scalars.csv",
     "Baseline K=0",           "baseline", 0, "avg",    1,  0),
    ("n100-attack-gw2-off20.csv",
     "Attack 2GW K=1 +20dB",   "attack",   1, "avg",    2, 20),
    ("n100-attack-gw2-off40.csv",
     "Attack 2GW K=1 +40dB",   "attack",   1, "avg",    2, 40),
    ("n100-gw2-defense-merged-off20.csv",
     "Defense 2GW K=1 +20dB",  "defense",  1, "secure", 2, 20),
    ("n100-gw2-defense-merged-off40.csv",
     "Defense 2GW K=1 +40dB",  "defense",  1, "secure", 2, 40),
    ("n100-gw3-K1-attack-merged-off20.csv",
     "Attack 3GW K=1 +20dB",   "attack",   1, "avg",    3, 20),
    ("n100-gw3-K1-attack-merged-off40.csv",
     "Attack 3GW K=1 +40dB",   "attack",   1, "avg",    3, 40),
    ("n100-gw3-K1-defense-merged-off20.csv",
     "Defense 3GW K=1 +20dB",  "defense",  1, "secure", 3, 20),
    ("n100-gw3-K1-defense-merged-off40.csv",
     "Defense 3GW K=1 +40dB",  "defense",  1, "secure", 3, 40),
    ("n100-gw3-K2-attack-merged-off20.csv",
     "Attack 3GW K=2 +20dB",   "attack",   2, "avg",    3, 20),
    ("n100-gw3-K2-attack-merged-off40.csv",
     "Attack 3GW K=2 +40dB",   "attack",   2, "avg",    3, 40),
    ("n100-gw3-K2-defense-merged-off20.csv",
     "Defense 3GW K=2 +20dB",  "defense",  2, "secure", 3, 20),
    ("n100-gw3-K2-defense-merged-off40.csv",
     "Defense 3GW K=2 +40dB",  "defense",  2, "secure", 3, 40),
]

# ── Auto-export map: CSV -> (run_range, sca_prefix) ───────────────────────────
EXPORT_MAP = {
    # ── N=100 original experiments ──
    "n100-attack-gw2-off20.csv":             (range(0, 5),  "n100-gw2-attack"),
    "n100-attack-gw2-off40.csv":             (range(5, 10), "n100-gw2-attack"),
    "n100-gw2-defense-merged-off20.csv":     (range(0, 5),  "n100-gw2-defense"),
    "n100-gw2-defense-merged-off40.csv":     (range(5, 10), "n100-gw2-defense"),
    "n100-gw3-K1-attack-merged-off20.csv":   (range(0, 5),  "n100-gw3-K1-attack"),
    "n100-gw3-K1-attack-merged-off40.csv":   (range(5, 10), "n100-gw3-K1-attack"),
    "n100-gw3-K1-defense-merged-off20.csv":  (range(0, 5),  "n100-gw3-K1-defense"),
    "n100-gw3-K1-defense-merged-off40.csv":  (range(5, 10), "n100-gw3-K1-defense"),
    "n100-gw3-K2-attack-merged-off20.csv":   (range(0, 5),  "n100-gw3-K2-attack"),
    "n100-gw3-K2-attack-merged-off40.csv":   (range(5, 10), "n100-gw3-K2-attack"),
    "n100-gw3-K2-defense-merged-off20.csv":  (range(0, 5),  "n100-gw3-K2-defense"),
    "n100-gw3-K2-defense-merged-off40.csv":  (range(5, 10), "n100-gw3-K2-defense"),
    # ── N=200 scalability ──
    "n200-3gw-k0-baseline.csv":              (range(0, 5),  "n200-3gw-k0-baseline"),
    "n200-3gw-K1-attack-off20.csv":          (range(0, 5),  "n200-3gw-K1-attack"),
    "n200-3gw-K1-attack-off40.csv":          (range(5, 10), "n200-3gw-K1-attack"),
    "n200-3gw-K1-defense-off20.csv":         (range(0, 5),  "n200-3gw-K1-defense"),
    "n200-3gw-K1-defense-off40.csv":         (range(5, 10), "n200-3gw-K1-defense"),
    # ── N=500 scalability ──
    "n500-3gw-k0-baseline.csv":              (range(0, 5),  "n500-3gw-k0-baseline"),
    "n500-3gw-K1-attack-off20.csv":          (range(0, 5),  "n500-3gw-K1-attack"),
    "n500-3gw-K1-attack-off40.csv":          (range(5, 10), "n500-3gw-K1-attack"),
    "n500-3gw-K1-defense-off20.csv":         (range(0, 5),  "n500-3gw-K1-defense"),
    "n500-3gw-K1-defense-off40.csv":         (range(5, 10), "n500-3gw-K1-defense"),
    # ── N=100 4GW ──
    "n100-gw4-K1-attack-off20.csv":          (range(0, 5),  "n100-gw4-K1-attack"),
    "n100-gw4-K1-attack-off40.csv":          (range(5, 10), "n100-gw4-K1-attack"),
    "n100-gw4-K1-defense-off20.csv":         (range(0, 5),  "n100-gw4-K1-defense"),
    "n100-gw4-K1-defense-off40.csv":         (range(5, 10), "n100-gw4-K1-defense"),
    # ── N=1000 scalability ──
    "n1000-3gw-k0-baseline.csv":             (range(0, 5),  "n1000-3gw-k0-baseline"),
    "n1000-3gw-K1-attack-off20.csv":         (range(0, 5),  "n1000-3gw-K1-attack"),
    "n1000-3gw-K1-attack-off40.csv":         (range(5, 10), "n1000-3gw-K1-attack"),
    "n1000-3gw-K1-defense-off20.csv":        (range(0, 5),  "n1000-3gw-K1-defense"),
    "n1000-3gw-K1-defense-off40.csv":        (range(5, 10), "n1000-3gw-K1-defense"),
    # ── Uniform topology (2 offsets × 2 adrMethods × 5 reps) ──
    "n100-uniform-attack-off20.csv":         (range(0, 5),   "n100-3gw-uniform"),
    "n100-uniform-defense-off20.csv":        (range(5, 10),  "n100-3gw-uniform"),
    "n100-uniform-attack-off40.csv":         (range(10, 15), "n100-3gw-uniform"),
    "n100-uniform-defense-off40.csv":        (range(15, 20), "n100-3gw-uniform"),
}

def try_export(csv_fname):
    """Export a CSV from .sca files if all needed .sca files exist."""
    if csv_fname not in EXPORT_MAP:
        return False
    runs, prefix = EXPORT_MAP[csv_fname]
    sca_files = [os.path.join(SCA_DIR, f"{prefix}-s{r}.ini.sca") for r in runs]
    missing_sca = [f for f in sca_files if not os.path.exists(f)]
    if missing_sca:
        print(f"  [SCA NOT READY] {os.path.basename(missing_sca[0])} (and {len(missing_sca)-1} more)")
        return False
    out_path  = os.path.join(RESULTS_DIR, csv_fname)
    sca_posix = " ".join(f.replace("\\", "/").replace("C:", "/c") for f in sca_files)
    out_posix = out_path.replace("\\", "/").replace("C:", "/c")
    path_setup = (
        "export PATH=/c/omnetpp/tools/win32.x86_64/mingw64/bin"
        ":/c/omnetpp/tools/win32.x86_64/usr/bin:/c/omnetpp/bin:$PATH"
        " && export __omnetpp_root_dir=/c/omnetpp"
    )
    bash_cmd  = f"{path_setup} && opp_scavetool export {sca_posix} -o {out_posix}"
    env = dict(os.environ, HOME="C:\\omnetpp\\", MSYSTEM="MINGW64")
    result = subprocess.run([BASH, "--login", "-c", bash_cmd],
                            capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(f"  [EXPORTED] {csv_fname}")
        return True
    print(f"  [EXPORT FAILED] {csv_fname}: {result.stderr[-200:]}")
    return False

# ── CSV loading ────────────────────────────────────────────────────────────────
def load_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 7 and row[1] == "scalar":
                rows.append(row)
    return rows

def vals(rows, name_fn, mod_fn=None):
    out = []
    for r in rows:
        if name_fn(r[3]) and (mod_fn is None or mod_fn(r[2])) \
                and r[6] not in ("", "nan", "NaN"):
            try:
                out.append(float(r[6]))
            except ValueError:
                pass
    return out

# ── Metric extraction ──────────────────────────────────────────────────────────
def extract(rows):
    ns_der   = vals(rows, lambda n: n == "LoRa_NS_DER")
    gw_der   = vals(rows, lambda n: n == "LoRa_GW_DER")
    final_sf = vals(rows, lambda n: n == "finalSF",
                   lambda m: "loRaNodes" in m)
    sent_all = vals(rows, lambda n: n == "LoRa_AppPacketSent:count",
                   lambda m: "loRaNodes" in m)
    retries  = vals(rows, lambda n: n == "numRetry",
                   lambda m: "loRaNodes" in m)

    energy_by_mod = {r[2]: float(r[6]) for r in rows
                     if r[3] == "totalEnergyConsumed"
                     and r[6] not in ("", "nan", "NaN")}
    sent_by_mod   = {r[2]: float(r[6]) for r in rows
                     if r[3] == "LoRa_AppPacketSent:count"
                     and r[6] not in ("", "nan", "NaN")}
    e_per_pkt = []
    for app_mod, sent in sent_by_mod.items():
        base = app_mod.rsplit(".", 1)[0]
        emod = base + ".LoRaNic.radio.energyConsumer"
        if emod in energy_by_mod and sent > 0:
            e_per_pkt.append(energy_by_mod[emod] / sent * 1000)

    sf_node    = {sf: sum(1 for v in final_sf if v == sf) for sf in range(7, 13)}
    total_sent = sum(sent_all)
    server_rcv = sum(vals(rows, lambda n: n == "LoRa_ServerPacketReceived:count"))
    collisions = sum(vals(rows, lambda n: n == "LoRaReceptionCollision:count"))

    return {
        "pdr":        (statistics.mean(ns_der) * 100) if ns_der else None,
        "gw_pdr":     (statistics.mean(gw_der) * 100) if gw_der else None,
        "avg_sf":     statistics.mean(final_sf) if final_sf else None,
        "sf12_pct":   (sf_node.get(12, 0) / len(final_sf) * 100) if final_sf else None,
        "avg_energy": statistics.mean(e_per_pkt) if e_per_pkt else None,
        "retry_rate": (sum(retries) / total_sent * 100) if total_sent and retries else 0.0,
        "sf_node":    sf_node,
        "n_nodes":    len(final_sf),
        "collisions": collisions,
        "total_sent": total_sent,
        "server_rcv": server_rcv,
    }

# ── Per-run extraction for confidence intervals ───────────────────────────────
import math

def extract_per_run(rows):
    """Group rows by run ID, extract metrics per run, return per-run values."""
    from collections import defaultdict
    runs = defaultdict(list)
    for r in rows:
        runs[r[0]].append(r)

    per_run = {"pdr": [], "avg_sf": [], "avg_energy": [], "collisions": []}
    for run_id in sorted(runs):
        m = extract(runs[run_id])
        if m["pdr"] is not None:
            per_run["pdr"].append(m["pdr"])
        if m["avg_sf"] is not None:
            per_run["avg_sf"].append(m["avg_sf"])
        if m["avg_energy"] is not None:
            per_run["avg_energy"].append(m["avg_energy"])
        per_run["collisions"].append(m["collisions"])
    return per_run

def ci95(values):
    """Return (mean, half-width of 95% CI) for a list of values."""
    n = len(values)
    if n < 2:
        return (values[0] if values else 0.0, 0.0)
    m = statistics.mean(values)
    s = statistics.stdev(values)
    hw = 1.96 * s / math.sqrt(n)
    return (m, hw)

# ── Load all available scenarios ───────────────────────────────────────────────
do_export = "--export" in sys.argv
loaded    = []
missing   = []

for (fname, label, stype, K, mode, gw, offset) in SCENARIOS:
    path = os.path.join(RESULTS_DIR, fname)
    if not os.path.exists(path):
        if do_export and try_export(fname):
            pass  # file now created, fall through
        else:
            missing.append(fname)
            continue
    rows = load_rows(path)
    m    = extract(rows)
    pr   = extract_per_run(rows)
    entry = dict(fname=fname, label=label, stype=stype, K=K,
                 mode=mode, gw=gw, offset=offset, per_run=pr, **m)
    # Attach CI values
    for key in ("pdr", "avg_sf", "avg_energy", "collisions"):
        mu, hw = ci95(pr[key]) if pr[key] else (0.0, 0.0)
        entry[f"{key}_ci"] = hw
        entry[f"{key}_std"] = statistics.stdev(pr[key]) if len(pr[key]) >= 2 else 0.0
    loaded.append(entry)
    pdr_s = f"{m['pdr']:.1f}%"        if m['pdr']        is not None else "N/A"
    sf_s  = f"{m['avg_sf']:.2f}"      if m['avg_sf']      is not None else "N/A"
    e_s   = f"{m['avg_energy']:.1f}mJ" if m['avg_energy'] is not None else "N/A"
    ci_s  = f"±{entry['pdr_ci']:.1f}"  if entry['pdr_ci'] > 0 else ""
    print(f"[OK]  {label:42s}  PDR={pdr_s:7s}{ci_s:>6s}  SF={sf_s}  E={e_s}")

if missing:
    print(f"\n[MISSING] {len(missing)} CSV files not yet available:")
    for f in missing:
        print(f"  {f}")
    print("  -> Once runs finish, re-run with --export to auto-export SCA files.")
    print()

if not loaded:
    print("No result files found. Nothing to analyse.")
    sys.exit(0)

# ── Helpers ────────────────────────────────────────────────────────────────────
STYPE_COLOUR = {"baseline": "green", "attack": "red",    "defense": "steelblue"}
STYPE_MARKER = {"baseline": "*",     "attack": "o",      "defense": "s"}

def nf(v, fmt="%.2f"):
    return (fmt % v) if v is not None else "N/A"

# ── Fig 1: SF distribution bar chart ──────────────────────────────────────────
def plot_sf_distribution(entries, out_stem):
    if not _PLOTS:
        return
    sfs = list(range(7, 13))
    x   = np.arange(len(sfs))
    w   = min(0.12, 0.75 / max(len(entries), 1))
    fig, ax = plt.subplots(figsize=(7.16, 2.8))
    for i, e in enumerate(entries):
        n    = e["n_nodes"] or 1
        pcts = [e["sf_node"].get(sf, 0) / n * 100 for sf in sfs]
        off  = (i - (len(entries) - 1) / 2) * w
        c    = STYPE_COLOUR.get(e["stype"], "grey")
        ax.bar(x + off, pcts, w, label=e["label"], color=c, alpha=0.8,
               edgecolor="white", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([f"SF{sf}" for sf in sfs], fontsize=8)
    ax.set_ylabel("Node share (%)", fontsize=9)
    ax.set_title("Final Spreading Factor Distribution", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.legend(fontsize=6, loc="upper right", ncol=2)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"{out_stem}.{ext}"), dpi=300)
    plt.close(fig)
    print(f"[PLOT] {out_stem}")

# ── Figs 2-5: Metric vs K ─────────────────────────────────────────────────────
def plot_metric_vs_K(entries, metric_key, ylabel, title, out_stem, offset_filter=20):
    if not _PLOTS:
        return
    sub = [e for e in entries
           if e["offset"] in (0, offset_filter) and e[metric_key] is not None]

    ci_key = f"{metric_key}_ci"

    def pts(stype):
        from collections import defaultdict
        groups = defaultdict(list)
        ci_groups = defaultdict(list)
        for e in sub:
            if e["stype"] == stype and e[metric_key] is not None:
                groups[e["K"]].append(e[metric_key])
                if ci_key in e:
                    ci_groups[e["K"]].append(e[ci_key])
        result = []
        for k in sorted(groups):
            mean_val = statistics.mean(groups[k])
            # Use propagated CI if available, else 0
            if ci_groups[k]:
                ci_val = statistics.mean(ci_groups[k])
            else:
                ci_val = 0.0
            result.append((k, mean_val, ci_val))
        return result

    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    bp = pts("baseline")
    if bp:
        bv = statistics.mean(v for _, v, _ in bp)
        ax.axhline(bv, color="green", ls="--", lw=1.5, label=f"Baseline ({bv:.2f})")

    for stype, lbl, ls in [("attack",  "ADR-Avg (attack)",   "-"),
                            ("defense", "ADR-Secure (defense)", "--")]:
        p = pts(stype)
        if not p:
            continue
        ks, vs, cis = zip(*p)
        ax.errorbar(ks, vs, yerr=cis, ls=ls, marker=STYPE_MARKER[stype],
                    color=STYPE_COLOUR[stype], lw=2, ms=6, capsize=3,
                    capthick=1.2, label=f"{lbl} ({offset_filter} dB)")

    ax.set_xlabel("Malicious gateways K", fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=9)
    ax.set_xticks([0, 1, 2])
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"{out_stem}.{ext}"), dpi=300)
    plt.close(fig)
    print(f"[PLOT] {out_stem}")

if "--no-plots" not in sys.argv:
    plot_sf_distribution(loaded, "fig1_sf_distribution")
    plot_metric_vs_K(loaded, "pdr",        "PDR (%)",
                     "PDR vs K",           "fig2_pdr_vs_K")
    plot_metric_vs_K(loaded, "avg_energy", "Energy per packet (mJ)",
                     "Energy vs K",        "fig3_energy_vs_K")
    plot_metric_vs_K(loaded, "avg_sf",     "Average final SF",
                     "Avg SF vs K",        "fig4_sf_mean_vs_K")
    plot_metric_vs_K(loaded, "collisions", "Total collisions",
                     "Collisions vs K",    "fig5_collisions_vs_K")

# ── Fig 6: Scalability — PDR vs N (baseline/attack/defense) ───────────────────
SCALE_SCENARIOS = [
    # N=200
    ("n200-3gw-k0-baseline.csv",
     "Baseline N=200",          "baseline", 0, "avg",    3, 0,  200),
    ("n200-3gw-K1-attack-off20.csv",
     "Attack N=200 K=1 +20dB",  "attack",   1, "avg",    3, 20, 200),
    ("n200-3gw-K1-defense-off20.csv",
     "Defense N=200 K=1 +20dB", "defense",  1, "secure", 3, 20, 200),
    # N=500
    ("n500-3gw-k0-baseline.csv",
     "Baseline N=500",          "baseline", 0, "avg",    3, 0,  500),
    ("n500-3gw-K1-attack-off20.csv",
     "Attack N=500 K=1 +20dB",  "attack",   1, "avg",    3, 20, 500),
    ("n500-3gw-K1-defense-off20.csv",
     "Defense N=500 K=1 +20dB", "defense",  1, "secure", 3, 20, 500),
    # N=1000
    ("n1000-3gw-k0-baseline.csv",
     "Baseline N=1000",         "baseline", 0, "avg",    3, 0,  1000),
    ("n1000-3gw-K1-attack-off20.csv",
     "Attack N=1000 K=1 +20dB", "attack",   1, "avg",    3, 20, 1000),
    ("n1000-3gw-K1-defense-off20.csv",
     "Defense N=1000 K=1 +20dB","defense",  1, "secure", 3, 20, 1000),
]

# ── Uniform topology scenarios ────────────────────────────────────────────────
UNIFORM_SCENARIOS = [
    ("n100-uniform-attack-off20.csv",
     "Uniform Attack +20dB",    "attack",   1, "avg",    3, 20),
    ("n100-uniform-defense-off20.csv",
     "Uniform Defense +20dB",   "defense",  1, "secure", 3, 20),
    ("n100-uniform-attack-off40.csv",
     "Uniform Attack +40dB",    "attack",   1, "avg",    3, 40),
    ("n100-uniform-defense-off40.csv",
     "Uniform Defense +40dB",   "defense",  1, "secure", 3, 40),
]

scale_loaded = []
for entry in SCALE_SCENARIOS:
    fname, label, stype, K, mode, gw, offset, N = entry
    path = os.path.join(RESULTS_DIR, fname)
    if not os.path.exists(path):
        if do_export and try_export(fname):
            pass
        else:
            continue
    if not os.path.exists(os.path.join(RESULTS_DIR, fname)):
        continue
    rows = load_rows(os.path.join(RESULTS_DIR, fname))
    m = extract(rows)
    pr = extract_per_run(rows)
    e = dict(fname=fname, label=label, stype=stype, K=K,
             mode=mode, gw=gw, offset=offset, N=N, per_run=pr, **m)
    for key in ("pdr", "avg_sf", "avg_energy", "collisions"):
        mu, hw = ci95(pr[key]) if pr[key] else (0.0, 0.0)
        e[f"{key}_ci"] = hw
    scale_loaded.append(e)
    print(f"[SCALE] {label:36s}  PDR={m['pdr']:.1f}%" if m['pdr'] else f"[SCALE] {label}: N/A")

# ── Load uniform topology results ─────────────────────────────────────────────
uniform_loaded = []
for entry in UNIFORM_SCENARIOS:
    fname, label, stype, K, mode, gw, offset = entry
    path = os.path.join(RESULTS_DIR, fname)
    if not os.path.exists(path):
        if do_export and try_export(fname):
            pass
        else:
            continue
    if not os.path.exists(os.path.join(RESULTS_DIR, fname)):
        continue
    rows = load_rows(os.path.join(RESULTS_DIR, fname))
    m = extract(rows)
    pr = extract_per_run(rows)
    e = dict(fname=fname, label=label, stype=stype, K=K,
             mode=mode, gw=gw, offset=offset, per_run=pr, **m)
    for key in ("pdr", "avg_sf", "avg_energy", "collisions"):
        mu, hw = ci95(pr[key]) if pr[key] else (0.0, 0.0)
        e[f"{key}_ci"] = hw
        e[f"{key}_std"] = statistics.stdev(pr[key]) if len(pr[key]) >= 2 else 0.0
    uniform_loaded.append(e)
    print(f"[UNIFORM] {label:36s}  PDR={m['pdr']:.1f}%" if m['pdr'] else f"[UNIFORM] {label}: N/A")

def plot_scalability(n100_entries, scale_entries, out_stem):
    """PDR vs N (100/200/500) for baseline, attack, defense at K=1 +20dB."""
    if not _PLOTS:
        return
    # Build N → PDR mapping for each stype
    from collections import defaultdict
    data = defaultdict(dict)  # stype → {N: (pdr, ci)}

    # N=100 from main results
    for e in n100_entries:
        if e["offset"] not in (0, 20) or e["pdr"] is None:
            continue
        if e["stype"] == "baseline" and e["K"] == 0:
            data["baseline"][100] = (e["pdr"], e.get("pdr_ci", 0))
        elif e["stype"] == "attack" and e["K"] == 1 and e["gw"] == 3:
            data["attack"][100] = (e["pdr"], e.get("pdr_ci", 0))
        elif e["stype"] == "defense" and e["K"] == 1 and e["gw"] == 3:
            data["defense"][100] = (e["pdr"], e.get("pdr_ci", 0))

    # N=200/500 from scale results
    for e in scale_entries:
        if e["pdr"] is None:
            continue
        data[e["stype"]][e["N"]] = (e["pdr"], e.get("pdr_ci", 0))

    if not any(data.values()):
        print(f"[SKIP] {out_stem} — no scalability data available yet")
        return

    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    for stype, lbl, ls in [("baseline", "Baseline (K=0)",       "--"),
                            ("attack",  "ADR-Avg (K=1, +20dB)", "-"),
                            ("defense", "ADR-Secure (K=1, +20dB)", "-")]:
        if stype not in data or not data[stype]:
            continue
        ns = sorted(data[stype].keys())
        pdrs = [data[stype][n][0] for n in ns]
        cis  = [data[stype][n][1] for n in ns]
        ax.errorbar(ns, pdrs, yerr=cis, ls=ls, marker=STYPE_MARKER[stype],
                    color=STYPE_COLOUR[stype], lw=2, ms=6, capsize=3,
                    capthick=1.2, label=lbl)

    ax.set_xlabel("Number of nodes (N)", fontsize=9)
    ax.set_ylabel("PDR (%)", fontsize=9)
    ax.set_title("PDR Scalability: Baseline vs Attack vs Defense", fontsize=9)
    ax.set_xticks([100, 200, 500, 1000])
    ax.tick_params(labelsize=8)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"{out_stem}.{ext}"), dpi=300)
    plt.close(fig)
    print(f"[PLOT] {out_stem}")

if "--no-plots" not in sys.argv:
    plot_scalability(loaded, scale_loaded, "fig6_scalability")

# ── Write scalability LaTeX table ──────────────────────────────────────────────
def write_scalability_table(n100_entries, scale_entries, out_path):
    lines = [
        r"\begin{table}[t]", r"\centering",
        r"\caption{Scalability: PDR (\%) at Different Network Sizes ($K=1$, +20\,dB)}",
        r"\label{tab:scalability}",
        r"\begin{tabular}{lcccc}", r"\toprule",
        r"Scenario & $N=100$ & $N=200$ & $N=500$ & $N=1000$ \\\\",
        r"\midrule",
    ]
    # Gather N=100 values
    n100_data = {}
    for e in n100_entries:
        if e["pdr"] is None:
            continue
        if e["stype"] == "baseline" and e["K"] == 0 and e["offset"] == 0:
            n100_data["baseline"] = e["pdr"]
        elif e["stype"] == "attack" and e["K"] == 1 and e["gw"] == 3 and e["offset"] == 20:
            n100_data["attack"] = e["pdr"]
        elif e["stype"] == "defense" and e["K"] == 1 and e["gw"] == 3 and e["offset"] == 20:
            n100_data["defense"] = e["pdr"]
    # Gather N=200/500/1000
    scale_data = {}
    for e in scale_entries:
        if e["pdr"] is None:
            continue
        scale_data[(e["stype"], e["N"])] = e["pdr"]

    def v(stype, N):
        return f'{scale_data[(stype, N)]:.1f}' if (stype, N) in scale_data else '---'

    for stype, lbl in [("baseline", "Baseline (K=0)"),
                        ("attack", r"Attack (K=1, +20\,dB)"),
                        ("defense", r"Defense (K=1, +20\,dB)")]:
        v100 = f'{n100_data.get(stype, 0):.1f}' if stype in n100_data else '---'
        lines.append(f"{lbl} & {v100} & {v(stype, 200)} & {v(stype, 500)} & {v(stype, 1000)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[TAB]  {out_path}")

write_scalability_table(loaded, scale_loaded, os.path.join(TAB_DIR, "table6_scalability.tex"))

# ── Write uniform topology summary table ──────────────────────────────────────
def write_uniform_table(entries, out_path):
    if not entries:
        print("[SKIP] uniform table — no data")
        return
    lines = [
        r"\begin{table}[t]", r"\centering",
        r"\caption{Uniform Topology Results ($N=100$, 3 GWs, $K=1$)}",
        r"\label{tab:uniform}",
        r"\begin{tabular}{lcccc}", r"\toprule",
        r"Scenario & PDR (\%) & Avg SF & Energy (mJ) & Collisions \\",
        r"\midrule",
    ]
    for e in entries:
        safe = e["label"].replace("&", r"\&")
        pdr = f'{e["pdr"]:.1f}' if e["pdr"] else "---"
        sf  = f'{e["avg_sf"]:.2f}' if e["avg_sf"] else "---"
        en  = f'{e["avg_energy"]:.1f}' if e["avg_energy"] else "---"
        col = f'{e["collisions"]:.0f}' if e["collisions"] else "---"
        lines.append(f"{safe} & {pdr} & {sf} & {en} & {col} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[TAB]  {out_path}")

write_uniform_table(uniform_loaded, os.path.join(TAB_DIR, "table7_uniform.tex"))

# ── LaTeX tables ───────────────────────────────────────────────────────────────
def write_latex_summary(entries, out_path):
    lines = [
        r"\begin{table*}[t]", r"\centering",
        r"\caption{Simulation Results: ADR-Avg vs.\ ADR-Secure "
        r"(5 repetitions, 100 nodes, 24\,h)}",
        r"\label{tab:results}",
        r"\begin{tabular}{llcccccc}", r"\toprule",
        r"Scenario & GWs & $K$ & ADR & PDR (\%) & Avg SF & E/pkt (mJ) & Coll. \\",
        r"\midrule",
    ]
    for e in entries:
        safe = e["label"].replace("&", r"\&")
        lines.append(
            f"{safe} & {e['gw']} & {e['K']} & \\texttt{{{e['mode']}}} & "
            f"{nf(e['pdr'],'%.1f')} & {nf(e['avg_sf'],'%.2f')} & "
            f"{nf(e['avg_energy'],'%.1f')} & {int(e['collisions'])} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[TAB]  {out_path}")

def write_latex_sf_table(entries, out_path):
    lines = [
        r"\begin{table}[t]", r"\centering",
        r"\caption{Final SF Node Distribution (\% of nodes)}",
        r"\label{tab:sf_dist}",
        r"\begin{tabular}{l" + "c" * 6 + "}", r"\toprule",
        r"Scenario & SF7 & SF8 & SF9 & SF10 & SF11 & SF12 \\", r"\midrule",
    ]
    for e in entries:
        n    = e["n_nodes"] or 1
        safe = e["label"].replace("&", r"\&")
        cells = [f"{e['sf_node'].get(sf,0)/n*100:.0f}\\%" for sf in range(7, 13)]
        lines.append(f"{safe} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[TAB]  {out_path}")

write_latex_summary(loaded, os.path.join(TAB_DIR, "table1_summary.tex"))
write_latex_sf_table(loaded, os.path.join(TAB_DIR, "table2_sf_distribution.tex"))

# ── Console summary ────────────────────────────────────────────────────────────
SEP = "-" * 92
lines = [
    "LoRaWAN ADR-Secure Experiment Results",
    f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
    SEP,
    f"{'Scenario':<44} {'PDR%':>7} {'GW-PDR':>7} {'SF':>6} {'E(mJ)':>8} {'Coll':>7}",
    SEP,
]
for e in loaded:
    lines.append(
        f"{e['label']:<44} {nf(e['pdr'],'%7.2f')} {nf(e['gw_pdr'],'%7.2f')} "
        f"{nf(e['avg_sf'],'%6.2f')} {nf(e['avg_energy'],'%8.2f')} {int(e['collisions']):>7}"
    )
lines.append(SEP)

# Per-SF delta for K=1, +20dB, 3GW
lines += ["", "SF delta: 3GW K=1 +20dB  Attack -> Defense"]
atk = next((e for e in loaded if e["stype"]=="attack"  and e["K"]==1
            and e["offset"]==20 and e["gw"]==3), None)
dfn = next((e for e in loaded if e["stype"]=="defense" and e["K"]==1
            and e["offset"]==20 and e["gw"]==3), None)
if atk and dfn:
    na = atk["n_nodes"] or 1
    nd = dfn["n_nodes"] or 1
    for sf in range(7, 13):
        ap = atk["sf_node"].get(sf, 0) / na * 100
        dp = dfn["sf_node"].get(sf, 0) / nd * 100
        lines.append(f"  SF{sf}: atk={ap:.0f}%  def={dp:.0f}%  d={dp-ap:+.0f}%")
else:
    lines.append("  (3GW K=1 data not yet available)")

summary = "\n".join(lines)
print("\n" + summary)
with open(os.path.join(RESULTS_DIR, "summary_console.txt"), "w", encoding="utf-8") as f:
    f.write(summary + "\n")

# ── Statistics table: mean ± std per scenario ─────────────────────────────────
stat_lines = [
    "",
    "=" * 100,
    "STATISTICS TABLE: Mean ± Std (95% CI)  [per-run aggregation, 5 seeds]",
    "=" * 100,
    f"{'Scenario':<36s} {'PDR (%)':>16s} {'Avg SF':>16s} {'E/pkt (mJ)':>16s} {'Collisions':>16s}",
    "-" * 100,
]
for e in loaded:
    parts = []
    for key in ("pdr", "avg_sf", "avg_energy", "collisions"):
        pr_vals = e["per_run"][key]
        if len(pr_vals) >= 2:
            mu = statistics.mean(pr_vals)
            sd = statistics.stdev(pr_vals)
            parts.append(f"{mu:>7.2f} ± {sd:<5.2f}")
        elif pr_vals:
            parts.append(f"{pr_vals[0]:>7.2f} ± {'N/A':<5s}")
        else:
            parts.append(f"{'N/A':>14s}")
    stat_lines.append(f"{e['label']:<36s} {parts[0]:>16s} {parts[1]:>16s} {parts[2]:>16s} {parts[3]:>16s}")
stat_lines.append("=" * 100)
stat_summary = "\n".join(stat_lines)
print(stat_summary)
with open(os.path.join(RESULTS_DIR, "statistics_table.txt"), "w", encoding="utf-8") as f:
    f.write(stat_summary + "\n")

# ── Scale / Uniform console summary ──────────────────────────────────────────
if scale_loaded:
    print("\n" + "=" * 80)
    print("SCALABILITY RESULTS (N=200/500)")
    print("=" * 80)
    print(f"{'Scenario':<36s} {'PDR%':>7s} {'Avg SF':>7s} {'E(mJ)':>8s}")
    print("-" * 80)
    for e in scale_loaded:
        print(f"{e['label']:<36s} {nf(e['pdr'],'%7.2f')} {nf(e['avg_sf'],'%7.2f')} {nf(e['avg_energy'],'%8.2f')}")

if uniform_loaded:
    print("\n" + "=" * 80)
    print("UNIFORM TOPOLOGY RESULTS")
    print("=" * 80)
    print(f"{'Scenario':<36s} {'PDR%':>7s} {'Avg SF':>7s} {'E(mJ)':>8s} {'Coll':>7s}")
    print("-" * 80)
    for e in uniform_loaded:
        print(f"{e['label']:<36s} {nf(e['pdr'],'%7.2f')} {nf(e['avg_sf'],'%7.2f')} {nf(e['avg_energy'],'%8.2f')} {int(e['collisions']):>7}")

# ── Energy analysis: total network energy + battery lifetime ──────────────────
BATTERY_MAH = 2000.0   # mAh
BATTERY_V   = 3.3      # V
BATTERY_J   = BATTERY_MAH * BATTERY_V * 3.6  # mAh × V × 3.6 = Joules (23760 J)

def compute_energy_metrics(entry, n_nodes=100):
    """Compute total network energy (J) and estimated battery lifetime (days).
    Normalizes by number of runs to get per-24h values."""
    e_per_pkt_mJ = entry.get("avg_energy")  # mJ per packet
    total_sent   = entry.get("total_sent", 0)
    if e_per_pkt_mJ is None or total_sent == 0:
        return None, None, None
    # Number of runs = number of per-run PDR values
    n_runs = len(entry.get("per_run", {}).get("pdr", [])) or 1
    # total_sent across all runs → per-run
    sent_per_run = total_sent / n_runs
    # Total energy for all nodes in one 24h run
    total_energy_J = e_per_pkt_mJ / 1000.0 * sent_per_run
    # Per-node daily energy
    per_node_daily_J = total_energy_J / n_nodes
    # Battery lifetime in days
    lifetime_days = BATTERY_J / per_node_daily_J if per_node_daily_J > 0 else float('inf')
    return total_energy_J, per_node_daily_J, lifetime_days

def write_energy_table(entries, out_path):
    lines = [
        r"\begin{table}[t]", r"\centering",
        r"\caption{Energy Overhead and Estimated Battery Lifetime"
        r" (2000\,mAh, 3.3\,V Li-Ion)}",
        r"\label{tab:energy}",
        r"\begin{tabular}{lcccc}", r"\toprule",
        r"Scenario & E/pkt (mJ) & Total (J) & Daily/node (J) & Lifetime (days) \\",
        r"\midrule",
    ]
    for e in entries:
        total_J, daily_J, life_d = compute_energy_metrics(e)
        safe = e["label"].replace("&", r"\&")
        if total_J is not None:
            lines.append(
                f"{safe} & {e['avg_energy']:.1f} & {total_J:.1f} & "
                f"{daily_J:.2f} & {life_d:.0f} \\\\"
            )
        else:
            lines.append(f"{safe} & N/A & N/A & N/A & {{N/A}} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[TAB]  {out_path}")

write_energy_table(loaded, os.path.join(TAB_DIR, "table3_energy_lifetime.tex"))

# Print energy summary to console
print("\n" + "=" * 85)
print("ENERGY & BATTERY LIFETIME ANALYSIS (2000 mAh, 3.3V)")
print("=" * 85)
print(f"{'Scenario':<36s} {'E/pkt':>8s} {'Total(J)':>10s} {'Daily/node':>12s} {'Lifetime':>12s}")
print("-" * 85)
for e in loaded:
    total_J, daily_J, life_d = compute_energy_metrics(e)
    if total_J is not None:
        print(f"{e['label']:<36s} {e['avg_energy']:>7.1f}mJ {total_J:>9.1f}J {daily_J:>10.2f}J {life_d:>10.0f}d")
print("=" * 85)

# ── paper_numbers.txt: key values for update_paper.py ─────────────────────────
def get_e(stype, K, gw, offset):
    return next((e for e in loaded if e["stype"]==stype and e["K"]==K
                 and e["gw"]==gw and e["offset"]==offset), None)

base    = get_e("baseline", 0, 1, 0)
atk2_20 = get_e("attack",  1, 2, 20)
atk2_40 = get_e("attack",  1, 2, 40)
dfn2_20 = get_e("defense", 1, 2, 20)
atk3_20 = get_e("attack",  1, 3, 20)
dfn3_20 = get_e("defense", 1, 3, 20)
atk3k2  = get_e("attack",  2, 3, 20)
dfn3k2  = get_e("defense", 2, 3, 20)

def N(e, key, fmt="{:.2f}"):
    return fmt.format(e[key]) if (e and e.get(key) is not None) else "MISSING"

pnums = [
    f"BASELINE_PDR={N(base,'pdr','{:.1f}')}",
    f"BASELINE_SF={N(base,'avg_sf')}",
    f"BASELINE_ENERGY={N(base,'avg_energy','{:.1f}')}",
    f"ATK2_20_PDR={N(atk2_20,'pdr','{:.1f}')}",
    f"ATK2_20_SF={N(atk2_20,'avg_sf')}",
    f"ATK2_20_ENERGY={N(atk2_20,'avg_energy','{:.1f}')}",
    f"ATK2_40_PDR={N(atk2_40,'pdr','{:.1f}')}",
    f"ATK2_40_SF={N(atk2_40,'avg_sf')}",
    f"DFN2_20_PDR={N(dfn2_20,'pdr','{:.1f}')}",
    f"DFN2_20_SF={N(dfn2_20,'avg_sf')}",
    f"ATK3_20_PDR={N(atk3_20,'pdr','{:.1f}')}",
    f"ATK3_20_SF={N(atk3_20,'avg_sf')}",
    f"DFN3_20_PDR={N(dfn3_20,'pdr','{:.1f}')}",
    f"DFN3_20_SF={N(dfn3_20,'avg_sf')}",
    f"ATK3K2_PDR={N(atk3k2,'pdr','{:.1f}')}",
    f"DFN3K2_PDR={N(dfn3k2,'pdr','{:.1f}')}",
]
with open(os.path.join(RESULTS_DIR, "paper_numbers.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(pnums) + "\n")
print(f"[NUM]  {os.path.join(RESULTS_DIR,'paper_numbers.txt')}")

print(f"\n[OK]  Figures -> {FIG_DIR}")
print(f"[OK]  Tables  -> {TAB_DIR}")
