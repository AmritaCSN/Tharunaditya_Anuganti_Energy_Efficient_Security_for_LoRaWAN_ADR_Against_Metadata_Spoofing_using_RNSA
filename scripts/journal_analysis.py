"""
journal_analysis.py — Extended analysis for journal-level ADR-Secure paper.

New experiments analysed:
  1. Defense ablation study (median_only vs abstain_only vs full secure)
  2. Adaptive attacker (step / random vs fixed offset)
  3. Gateway-density sensitivity (N=3/4/5 GWs, varying K)

Usage:
    python scripts/journal_analysis.py             # requires CSVs in results/
    python scripts/journal_analysis.py --export    # auto-export .sca → CSV first
    python scripts/journal_analysis.py --no-plots  # tables only

Outputs (results/figures/ and results/tables/):
    fig_ablation_bars.pdf/png       — PDR bar chart comparing defense variants
    fig_adaptive_attacker.pdf/png   — PDR vs attack strength (fixed/step/random)
    fig_gw_density.pdf/png          — PDR vs gateway count / Byzantine fraction
    table_ablation.tex              — LaTeX table: ablation study results
    table_adaptive.tex              — LaTeX table: adaptive attacker results
    table_gw_density.tex            — LaTeX table: gateway density results
    table_full_inventory.tex        — Complete experiment inventory (all runs)
"""

import sys, io, os, csv, math, statistics, subprocess
from collections import defaultdict

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

_PLOTS = True
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
except ImportError:
    _PLOTS = False
    print("[WARN] matplotlib/numpy not installed — plots skipped.")

# ── Paths ──────────────────────────────────────────────────────────────────────
RESULTS_DIR = r"C:\omnet-workspace\results"
SCA_DIR     = r"C:\omnet-workspace\flora\simulations\results"
FIG_DIR     = os.path.join(RESULTS_DIR, "figures")
TAB_DIR     = os.path.join(RESULTS_DIR, "tables")
BASH        = r"C:\omnetpp\tools\win32.x86_64\usr\bin\bash.exe"
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TAB_DIR, exist_ok=True)

# ── Scenario registries ────────────────────────────────────────────────────────
# (csv_stem, label, group, K, adr_method, gw_count, offset_dB)

# Reference scenarios from original paper (for comparison columns)
REF_SCENARIOS = [
    ("n100-gw3-K1-attack-merged-off20",  "No Defense +20dB",       "ref",    1, "avg",    3, 20),
    ("n100-gw3-K1-attack-merged-off40",  "No Defense +40dB",       "ref",    1, "avg",    3, 40),
    ("n100-gw3-K1-defense-merged-off20", "ADR-Secure +20dB",       "ref",    1, "secure", 3, 20),
    ("n100-gw3-K1-defense-merged-off40", "ADR-Secure +40dB",       "ref",    1, "secure", 3, 40),
]

# 1. Ablation study — 3 GWs, K=1, offset swept {20,40} dB
ABLATION_SCENARIOS = [
    ("n100-gw3-K1-median-only-off20",    "Median-Only +20dB",      "ablation", 1, "median_only",  3, 20),
    ("n100-gw3-K1-median-only-off40",    "Median-Only +40dB",      "ablation", 1, "median_only",  3, 40),
    ("n100-gw3-K1-abstain-only-off20",   "Abstain-Only +20dB",     "ablation", 1, "abstain_only", 3, 20),
    ("n100-gw3-K1-abstain-only-off40",   "Abstain-Only +40dB",     "ablation", 1, "abstain_only", 3, 40),
]

# 2. Adaptive attacker — 3 GWs, K=1
ADAPTIVE_SCENARIOS = [
    ("n100-gw3-K1-adaptive-step-attack",   "Step Atk / No Def",    "adaptive", 1, "avg",    3, -1),
    ("n100-gw3-K1-adaptive-step-defense",  "Step Atk / Secure",    "adaptive", 1, "secure", 3, -1),
    ("n100-gw3-K1-adaptive-random-attack", "Rand Atk / No Def",    "adaptive", 1, "avg",    3, -1),
    ("n100-gw3-K1-adaptive-random-defense","Rand Atk / Secure",    "adaptive", 1, "secure", 3, -1),
]

# 3. Gateway density study
GW_DENSITY_SCENARIOS = [
    # N=4 GWs, K=1 (25% Byzantine — within BFT bound)
    ("n100-gw4-K1-attack-off20",    "4GW K=1 Atk +20dB",  "gw_density", 1, "avg",    4, 20),
    ("n100-gw4-K1-attack-off40",    "4GW K=1 Atk +40dB",  "gw_density", 1, "avg",    4, 40),
    ("n100-gw4-K1-defense-off20",   "4GW K=1 Def +20dB",  "gw_density", 1, "secure", 4, 20),
    ("n100-gw4-K1-defense-off40",   "4GW K=1 Def +40dB",  "gw_density", 1, "secure", 4, 40),
    # N=5 GWs, K=2 (40% — within BFT bound)
    ("n100-gw5-K2-attack-off20",    "5GW K=2 Atk +20dB",  "gw_density", 2, "avg",    5, 20),
    ("n100-gw5-K2-attack-off40",    "5GW K=2 Atk +40dB",  "gw_density", 2, "avg",    5, 40),
    ("n100-gw5-K2-defense-off20",   "5GW K=2 Def +20dB",  "gw_density", 2, "secure", 5, 20),
    ("n100-gw5-K2-defense-off40",   "5GW K=2 Def +40dB",  "gw_density", 2, "secure", 5, 40),
    # N=5 GWs, K=3 (60% — beyond BFT bound, expected to degrade)
    ("n100-gw5-K3-attack-off20",    "5GW K=3 Atk +20dB",  "gw_density", 3, "avg",    5, 20),
    ("n100-gw5-K3-attack-off40",    "5GW K=3 Atk +40dB",  "gw_density", 3, "avg",    5, 40),
    ("n100-gw5-K3-defense-off20",   "5GW K=3 Def +20dB",  "gw_density", 3, "secure", 5, 20),
    ("n100-gw5-K3-defense-off40",   "5GW K=3 Def +40dB",  "gw_density", 3, "secure", 5, 40),
]

# Export map: csv_stem -> (run_range, sca_prefix)
EXPORT_MAP = {
    # Ablation (runs 0-4 = +20dB, runs 5-9 = +40dB)
    "n100-gw3-K1-median-only-off20":    (range(0, 5),  "n100-gw3-K1-median-only"),
    "n100-gw3-K1-median-only-off40":    (range(5, 10), "n100-gw3-K1-median-only"),
    "n100-gw3-K1-abstain-only-off20":   (range(0, 5),  "n100-gw3-K1-abstain-only"),
    "n100-gw3-K1-abstain-only-off40":   (range(5, 10), "n100-gw3-K1-abstain-only"),
    # Adaptive (5 reps, no offset sweep)
    "n100-gw3-K1-adaptive-step-attack":   (range(0, 5), "n100-gw3-K1-adaptive-step-attack"),
    "n100-gw3-K1-adaptive-step-defense":  (range(0, 5), "n100-gw3-K1-adaptive-step-defense"),
    "n100-gw3-K1-adaptive-random-attack": (range(0, 5), "n100-gw3-K1-adaptive-random-attack"),
    "n100-gw3-K1-adaptive-random-defense":(range(0, 5), "n100-gw3-K1-adaptive-random-defense"),
    # Gateway density (runs 0-4 = +20dB, runs 5-9 = +40dB)
    "n100-gw4-K1-attack-off20":   (range(0, 5),  "n100-gw4-K1-attack"),
    "n100-gw4-K1-attack-off40":   (range(5, 10), "n100-gw4-K1-attack"),
    "n100-gw4-K1-defense-off20":  (range(0, 5),  "n100-gw4-K1-defense"),
    "n100-gw4-K1-defense-off40":  (range(5, 10), "n100-gw4-K1-defense"),
    "n100-gw5-K2-attack-off20":   (range(0, 5),  "n100-gw5-K2-attack"),
    "n100-gw5-K2-attack-off40":   (range(5, 10), "n100-gw5-K2-attack"),
    "n100-gw5-K2-defense-off20":  (range(0, 5),  "n100-gw5-K2-defense"),
    "n100-gw5-K2-defense-off40":  (range(5, 10), "n100-gw5-K2-defense"),
    "n100-gw5-K3-attack-off20":   (range(0, 5),  "n100-gw5-K3-attack"),
    "n100-gw5-K3-attack-off40":   (range(5, 10), "n100-gw5-K3-attack"),
    "n100-gw5-K3-defense-off20":  (range(0, 5),  "n100-gw5-K3-defense"),
    "n100-gw5-K3-defense-off40":  (range(5, 10), "n100-gw5-K3-defense"),
}

# ── Export helper ──────────────────────────────────────────────────────────────
def try_export(csv_stem):
    if csv_stem not in EXPORT_MAP:
        return False
    runs, prefix = EXPORT_MAP[csv_stem]
    sca_files = [os.path.join(SCA_DIR, f"{prefix}-s{r}.ini.sca") for r in runs]
    missing   = [f for f in sca_files if not os.path.exists(f)]
    if missing:
        print(f"  [SCA NOT READY] {os.path.basename(missing[0])} (and {len(missing)-1} more)")
        return False
    out_path  = os.path.join(RESULTS_DIR, csv_stem + ".csv")
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
        print(f"  [EXPORTED] {csv_stem}.csv")
        return True
    print(f"  [EXPORT FAILED] {csv_stem}: {result.stderr[-300:]}")
    return False

# ── CSV loading ────────────────────────────────────────────────────────────────
def load_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh):
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
    final_sf = vals(rows, lambda n: n == "finalSF",   lambda m: "loRaNodes" in m)
    sent_all = vals(rows, lambda n: n == "LoRa_AppPacketSent:count",
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

    collisions = sum(vals(rows, lambda n: n == "LoRaReceptionCollision:count"))
    sf_node    = {sf: sum(1 for v in final_sf if v == sf) for sf in range(7, 13)}

    return {
        "pdr":        (statistics.mean(ns_der) * 100) if ns_der else None,
        "avg_sf":     statistics.mean(final_sf)       if final_sf else None,
        "avg_energy": statistics.mean(e_per_pkt)      if e_per_pkt else None,
        "collisions": collisions,
        "sf_node":    sf_node,
        "n_nodes":    len(final_sf),
    }

def extract_per_run(rows):
    runs = defaultdict(list)
    for r in rows:
        runs[r[0]].append(r)
    per_run = {"pdr": [], "avg_sf": [], "avg_energy": [], "collisions": []}
    for run_id in sorted(runs):
        m = extract(runs[run_id])
        for k in per_run:
            v = m.get(k)
            if v is not None:
                per_run[k].append(v)
    return per_run

def ci95(values):
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    if n == 1:
        return (values[0], 0.0)
    m  = statistics.mean(values)
    s  = statistics.stdev(values)
    hw = 1.96 * s / math.sqrt(n)
    return (m, hw)

# ── Load scenarios ─────────────────────────────────────────────────────────────
do_export = "--export" in sys.argv
no_plots  = "--no-plots" in sys.argv
if no_plots:
    _PLOTS = False

def load_all(scenarios):
    loaded, missing = [], []
    for (stem, label, group, K, mode, gw, offset) in scenarios:
        path = os.path.join(RESULTS_DIR, stem + ".csv")
        if not os.path.exists(path):
            if do_export and try_export(stem):
                pass
            else:
                missing.append(stem)
                continue
        rows = load_rows(path)
        m    = extract(rows)
        pr   = extract_per_run(rows)
        entry = dict(stem=stem, label=label, group=group, K=K,
                     mode=mode, gw=gw, offset=offset, per_run=pr, **m)
        for key in ("pdr", "avg_sf", "avg_energy", "collisions"):
            mu, hw = ci95(pr[key]) if pr[key] else (0.0, 0.0)
            entry[f"{key}_mean"] = mu
            entry[f"{key}_ci"]   = hw
        loaded.append(entry)
        pdr_s = f"{m['pdr']:.1f}%" if m['pdr'] is not None else "N/A"
        ci_s  = f" ±{entry['pdr_ci']:.2f}" if entry['pdr_ci'] > 0 else ""
        sf_s  = f"{m['avg_sf']:.2f}" if m['avg_sf'] is not None else "N/A"
        print(f"  [OK]  {label:42s}  PDR={pdr_s}{ci_s}  SF={sf_s}")
    if missing:
        print(f"  [MISSING {len(missing)}] ", ", ".join(missing[:4]),
              "..." if len(missing) > 4 else "")
    return loaded

print("\n── Loading reference scenarios ──────────────────────────────────────────")
ref_data     = load_all(REF_SCENARIOS)
print("\n── Loading ablation scenarios ───────────────────────────────────────────")
ablation_data = load_all(ABLATION_SCENARIOS)
print("\n── Loading adaptive attacker scenarios ──────────────────────────────────")
adaptive_data = load_all(ADAPTIVE_SCENARIOS)
print("\n── Loading gateway density scenarios ────────────────────────────────────")
gwdensity_data = load_all(GW_DENSITY_SCENARIOS)

# ── Helper: find entry by stem ─────────────────────────────────────────────────
def find(data, stem_substr):
    for e in data:
        if stem_substr in e["stem"]:
            return e
    return None

def pdr(e):
    return e["pdr"] if e and e["pdr"] is not None else 0.0

def pdr_ci(e):
    return e["pdr_ci"] if e else 0.0

def sf(e):
    return e["avg_sf"] if e and e["avg_sf"] is not None else 0.0

# ── FIGURE 1: Ablation bar chart ───────────────────────────────────────────────
def plot_ablation_bars(ref_data, ablation_data):
    if not _PLOTS:
        return
    # 4 defense variants × 2 offsets
    variants = [
        ("No Defense",    "atk",    "avg",          ref_data),
        ("Abstain-Only",  "abs",    "abstain_only",  ablation_data),
        ("Median-Only",   "med",    "median_only",   ablation_data),
        ("ADR-Secure",    "sec",    "secure",        ref_data),
    ]
    offsets = [20, 40]
    colors20 = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4"]
    colors40 = ["#e89898", "#ffbe78", "#86d086", "#80bddd"]

    x     = np.arange(len(variants))
    width = 0.35
    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    for oi, (off, clist) in enumerate([(20, colors20), (40, colors40)]):
        pdrs, cis = [], []
        for name, key, mode, data in variants:
            # find the entry matching offset and mode
            entry = next((e for e in data
                          if e["offset"] == off and e["mode"] == mode), None)
            pdrs.append(pdr(entry))
            cis.append(pdr_ci(entry))
        bars = ax.bar(x + (oi - 0.5) * width, pdrs, width,
                      color=clist,
                      label=f"+{off} dB offset",
                      alpha=0.9, edgecolor="white", linewidth=0.5)
        ax.errorbar(x + (oi - 0.5) * width, pdrs,
                    yerr=cis, fmt="none", capsize=3,
                    color="black", linewidth=1.2, zorder=5)

    ax.set_xlabel("Defense Variant", fontsize=9)
    ax.set_ylabel("Packet Delivery Ratio (%)", fontsize=9)
    ax.set_title("Ablation Study: Contribution of Each Defense Component\n"
                 "(3 GWs, N=100 nodes, K=1 Byzantine GW)", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([v[0] for v in variants], fontsize=8)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.axhline(87.3, color="gray", linestyle=":", linewidth=1.2,
               label="Baseline PDR (no attack, 87.3%)")
    ax.legend(fontsize=7)
    ax.grid(axis="y", alpha=0.3)
    for fmt in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"fig_ablation_bars.{fmt}"),
                    bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("[FIG] fig_ablation_bars saved")

# ── FIGURE 2: Adaptive attacker ────────────────────────────────────────────────
def plot_adaptive_attacker(ref_data, adaptive_data):
    if not _PLOTS:
        return
    # Compare PDR under 3 attacker strategies: fixed +20, step 0→40, random [10,40]
    def get(data, stem_part):
        e = next((x for x in data if stem_part in x["stem"]), None)
        return (pdr(e), pdr_ci(e))

    categories = [
        ("Fixed\n+20 dB",   "n100-gw3-K1-attack-merged-off20", ref_data,
                            "n100-gw3-K1-defense-merged-off20", ref_data),
        ("Fixed\n+40 dB",   "n100-gw3-K1-attack-merged-off40", ref_data,
                            "n100-gw3-K1-defense-merged-off40", ref_data),
        ("Step\n0→40 dB",  "adaptive-step-attack",   adaptive_data,
                            "adaptive-step-defense",  adaptive_data),
        ("Random\n[10,40]", "adaptive-random-attack", adaptive_data,
                            "adaptive-random-defense", adaptive_data),
    ]

    x     = np.arange(len(categories))
    width = 0.35
    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    atk_pdrs, atk_cis, def_pdrs, def_cis = [], [], [], []
    for _, atk_stem, atk_d, def_stem, def_d in categories:
        ap, ac = get(atk_d, atk_stem)
        dp, dc = get(def_d, def_stem)
        atk_pdrs.append(ap); atk_cis.append(ac)
        def_pdrs.append(dp); def_cis.append(dc)

    ax.bar(x - width/2, atk_pdrs, width, label="Under Attack (avg)",
           color="#d62728", alpha=0.85)
    ax.errorbar(x - width/2, atk_pdrs, yerr=atk_cis,
                fmt="none", capsize=3, color="black", linewidth=1.2)
    ax.bar(x + width/2, def_pdrs, width, label="ADR-Secure Defense",
           color="#1f77b4", alpha=0.85)
    ax.errorbar(x + width/2, def_pdrs, yerr=def_cis,
                fmt="none", capsize=3, color="black", linewidth=1.2)

    ax.axhline(87.3, color="gray", linestyle=":", linewidth=1.2,
               label="Baseline PDR (87.3%)")
    ax.set_xlabel("Attack Strategy", fontsize=9)
    ax.set_ylabel("Packet Delivery Ratio (%)", fontsize=9)
    ax.set_title("PDR Under Fixed vs Adaptive Byzantine Attacks\n"
                 "(3 GWs, N=100 nodes, K=1 Byzantine GW)", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([c[0] for c in categories], fontsize=8)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.legend(fontsize=7)
    ax.grid(axis="y", alpha=0.3)
    for fmt in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"fig_adaptive_attacker.{fmt}"),
                    bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("[FIG] fig_adaptive_attacker saved")

# ── FIGURE 3: Gateway density ──────────────────────────────────────────────────
def plot_gw_density(ref_data, gwdensity_data):
    if not _PLOTS:
        return
    # PDR vs (N_GW, K) for +20 dB attack and defense, across N=3,4,5 GWs
    configs = [
        (3, 1, "n100-gw3-K1-attack-merged-off20",  ref_data,
                "n100-gw3-K1-defense-merged-off20", ref_data, True),
        (4, 1, "n100-gw4-K1-attack-off20",         gwdensity_data,
                "n100-gw4-K1-defense-off20",        gwdensity_data, True),
        (5, 2, "n100-gw5-K2-attack-off20",         gwdensity_data,
                "n100-gw5-K2-defense-off20",        gwdensity_data, True),
        (5, 3, "n100-gw5-K3-attack-off20",         gwdensity_data,
                "n100-gw5-K3-defense-off20",        gwdensity_data, False),
    ]

    fig, ax = plt.subplots(figsize=(7.16, 3.0))
    xlabel_labels, atk_pdrs, atk_cis, def_pdrs, def_cis, within_bound = [], [], [], [], [], []

    for n_gw, k, atk_stem, atk_d, def_stem, def_d, in_bound in configs:
        frac = k / n_gw * 100
        xlabel_labels.append(f"N={n_gw}\nK={k}\n({frac:.0f}%)")
        ae = next((e for e in atk_d if atk_stem in e["stem"]), None)
        de = next((e for e in def_d if def_stem in e["stem"]), None)
        atk_pdrs.append(pdr(ae));  atk_cis.append(pdr_ci(ae))
        def_pdrs.append(pdr(de));  def_cis.append(pdr_ci(de))
        within_bound.append(in_bound)

    x = np.arange(len(configs))
    w = 0.35

    # Shade beyond-bound region
    for i, ib in enumerate(within_bound):
        if not ib:
            ax.axvspan(i - 0.5, i + 0.5, alpha=0.08, color="red",
                       label="_Beyond BFT bound")

    bars_atk = ax.bar(x - w/2, atk_pdrs, w, color="#d62728",
                       label="Under Attack", alpha=0.85)
    ax.errorbar(x - w/2, atk_pdrs, yerr=atk_cis,
                fmt="none", capsize=3, color="black", linewidth=1.2)
    bars_def = ax.bar(x + w/2, def_pdrs, w, color="#1f77b4",
                       label="ADR-Secure", alpha=0.85)
    ax.errorbar(x + w/2, def_pdrs, yerr=def_cis,
                fmt="none", capsize=3, color="black", linewidth=1.2)

    # Mark beyond-bound bars with hatch
    for i, ib in enumerate(within_bound):
        if not ib:
            bars_def[i].set_hatch("//")
            bars_def[i].set_edgecolor("red")

    ax.axhline(87.3, color="gray", linestyle=":", linewidth=1.2,
               label="Baseline PDR (87.3%)")
    ax.axvline(2.5, color="red", linestyle="--", linewidth=1.2, alpha=0.6,
               label="BFT bound exceeded →")
    ax.set_xlabel("Gateway Count N / Byzantine Count K", fontsize=9)
    ax.set_ylabel("Packet Delivery Ratio (%)", fontsize=9)
    ax.set_title("ADR-Secure PDR vs Gateway Density and Byzantine Fraction\n"
                 "(N=100 nodes, +20 dB offset, 5 repetitions)", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(xlabel_labels, fontsize=8)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.legend(fontsize=7, loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    for fmt in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"fig_gw_density.{fmt}"),
                    bbox_inches="tight", dpi=300)
    plt.close(fig)
    print("[FIG] fig_gw_density saved")

# ── TABLE: Ablation study ──────────────────────────────────────────────────────
def table_ablation(ref_data, ablation_data):
    rows_tex = []
    rows_tex.append(r"\begin{table}[t]")
    rows_tex.append(r"\centering")
    rows_tex.append(r"\caption{Defense Ablation Study: PDR (\%) Under K=1 Byzantine Attack "
                    r"(3 Gateways, N=100 nodes, 5 repetitions each).}")
    rows_tex.append(r"\label{tab:ablation}")
    rows_tex.append(r"\begin{tabular}{lcccc}")
    rows_tex.append(r"\hline")
    rows_tex.append(r"Defense Variant & +20 dB PDR & +40 dB PDR & Avg SF & Energy (mJ/pkt) \\")
    rows_tex.append(r"\hline")

    variants = [
        ("No Defense",   "avg",          ref_data),
        ("Abstain-Only", "abstain_only",  ablation_data),
        ("Median-Only",  "median_only",   ablation_data),
        ("ADR-Secure",   "secure",        ref_data),
    ]
    for name, mode, data in variants:
        e20 = next((e for e in data if e["mode"]==mode and e["offset"]==20), None)
        e40 = next((e for e in data if e["mode"]==mode and e["offset"]==40), None)
        p20 = f"{pdr(e20):.1f} $\\pm$ {pdr_ci(e20):.2f}" if e20 else "--"
        p40 = f"{pdr(e40):.1f} $\\pm$ {pdr_ci(e40):.2f}" if e40 else "--"
        sf_ = f"{sf(e20):.2f}" if e20 else "--"
        en_ = f"{e20['avg_energy']:.1f}" if e20 and e20['avg_energy'] else "--"
        rows_tex.append(f"{name} & {p20} & {p40} & {sf_} & {en_} \\\\")

    rows_tex.append(r"\hline")
    rows_tex.append(r"\multicolumn{5}{l}{\footnotesize BFT bound: $K < N_{GW}/2$ guarantees robustness.} \\")
    rows_tex.append(r"\end{tabular}")
    rows_tex.append(r"\end{table}")

    path = os.path.join(TAB_DIR, "table_ablation.tex")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows_tex))
    print(f"[TAB] table_ablation.tex written")

# ── TABLE: Adaptive attacker ───────────────────────────────────────────────────
def table_adaptive(ref_data, adaptive_data):
    rows_tex = []
    rows_tex.append(r"\begin{table}[t]")
    rows_tex.append(r"\centering")
    rows_tex.append(r"\caption{PDR (\%) Under Fixed vs.\ Adaptive Byzantine Attacks "
                    r"(3 GWs, N=100 nodes, K=1, 5 repetitions).}")
    rows_tex.append(r"\label{tab:adaptive}")
    rows_tex.append(r"\begin{tabular}{llcc}")
    rows_tex.append(r"\hline")
    rows_tex.append(r"Attack Strategy & Defense & PDR (\%) & Avg SF \\")
    rows_tex.append(r"\hline")

    configs = [
        ("Fixed +20 dB",   "n100-gw3-K1-attack-merged-off20",  ref_data,
                            "n100-gw3-K1-defense-merged-off20", ref_data),
        ("Fixed +40 dB",   "n100-gw3-K1-attack-merged-off40",  ref_data,
                            "n100-gw3-K1-defense-merged-off40", ref_data),
        ("Step 0$\\to$40 dB","adaptive-step-attack",  adaptive_data,
                             "adaptive-step-defense", adaptive_data),
        ("Random [10,40] dB","adaptive-random-attack",  adaptive_data,
                              "adaptive-random-defense", adaptive_data),
    ]
    first = True
    for atk_label, atk_stem, atk_d, def_stem, def_d in configs:
        ae = next((e for e in atk_d if atk_stem in e["stem"]), None)
        de = next((e for e in def_d if def_stem in e["stem"]), None)
        if not first:
            rows_tex.append(r"\hline")
        first = False
        for label, entry in [("None (avg)", ae), ("ADR-Secure", de)]:
            p  = f"{pdr(entry):.1f} $\\pm$ {pdr_ci(entry):.2f}" if entry else "--"
            s_ = f"{sf(entry):.2f}" if entry else "--"
            rows_tex.append(f"{atk_label} & {label} & {p} & {s_} \\\\")
            atk_label = ""  # blank for continuation rows

    rows_tex.append(r"\hline")
    rows_tex.append(r"\end{tabular}")
    rows_tex.append(r"\end{table}")

    path = os.path.join(TAB_DIR, "table_adaptive.tex")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows_tex))
    print(f"[TAB] table_adaptive.tex written")

# ── TABLE: Gateway density ─────────────────────────────────────────────────────
def table_gw_density(ref_data, gwdensity_data):
    rows_tex = []
    rows_tex.append(r"\begin{table}[t]")
    rows_tex.append(r"\centering")
    rows_tex.append(r"\caption{PDR (\%) vs.\ Gateway Count and Byzantine Fraction "
                    r"(N=100 nodes, +20/+40 dB offset, 5 reps each). "
                    r"$\dagger$ = BFT bound violated ($K \geq N_{GW}/2$).}")
    rows_tex.append(r"\label{tab:gw_density}")
    rows_tex.append(r"\begin{tabular}{cclcccc}")
    rows_tex.append(r"\hline")
    rows_tex.append(r"$N_{GW}$ & $K$ & Defense & +20 dB PDR & +40 dB PDR & Avg SF & In Bound \\")
    rows_tex.append(r"\hline")

    configs = [
        (3, 1, True,  ref_data,        ref_data),
        (4, 1, True,  gwdensity_data,  gwdensity_data),
        (5, 2, True,  gwdensity_data,  gwdensity_data),
        (5, 3, False, gwdensity_data,  gwdensity_data),
    ]
    for n_gw, k, in_bound, atk_d, def_d in configs:
        bound_str = r"\checkmark" if in_bound else r"$\dagger$"
        pfx = f"gw{n_gw}-K{k}"
        if n_gw == 3:
            atk20s = "n100-gw3-K1-attack-merged-off20"
            def20s = "n100-gw3-K1-defense-merged-off20"
            atk40s = "n100-gw3-K1-attack-merged-off40"
            def40s = "n100-gw3-K1-defense-merged-off40"
        else:
            atk20s = f"n100-gw{n_gw}-K{k}-attack-off20"
            def20s = f"n100-gw{n_gw}-K{k}-defense-off20"
            atk40s = f"n100-gw{n_gw}-K{k}-attack-off40"
            def40s = f"n100-gw{n_gw}-K{k}-defense-off40"

        ae20 = next((e for e in atk_d if atk20s in e["stem"]), None)
        de20 = next((e for e in def_d if def20s in e["stem"]), None)
        ae40 = next((e for e in atk_d if atk40s in e["stem"]), None)
        de40 = next((e for e in def_d if def40s in e["stem"]), None)

        def fmt_p(e):
            if e is None: return "--"
            return f"{pdr(e):.1f}$\\pm${pdr_ci(e):.2f}"

        rows_tex.append(
            f"\\multirow{{2}}{{*}}{{{n_gw}}} & \\multirow{{2}}{{*}}{{{k}}} & "
            f"No Defense & {fmt_p(ae20)} & {fmt_p(ae40)} & "
            f"{sf(ae20):.2f} & {bound_str} \\\\"
        )
        rows_tex.append(
            f" & & ADR-Secure & {fmt_p(de20)} & {fmt_p(de40)} & "
            f"{sf(de20):.2f} & {bound_str} \\\\"
        )
        rows_tex.append(r"\hline")

    rows_tex.append(r"\end{tabular}")
    rows_tex.append(r"\end{table}")

    path = os.path.join(TAB_DIR, "table_gw_density.tex")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows_tex))
    print(f"[TAB] table_gw_density.tex written")

# ── TABLE: Full experiment inventory ──────────────────────────────────────────
def table_full_inventory(ref_data, ablation_data, adaptive_data, gwdensity_data):
    all_data = ref_data + ablation_data + adaptive_data + gwdensity_data
    rows_tex = []
    rows_tex.append(r"\begin{table*}[t]")
    rows_tex.append(r"\centering")
    rows_tex.append(r"\caption{Complete Experiment Inventory — All Journal Simulation Scenarios.}")
    rows_tex.append(r"\label{tab:full_inventory}")
    rows_tex.append(r"\begin{tabular}{llccccc}")
    rows_tex.append(r"\hline")
    rows_tex.append(
        r"Scenario & Defense & $N_{GW}$ & $K$ & Offset (dB) & PDR (\%) & Avg SF \\")
    rows_tex.append(r"\hline")

    for e in all_data:
        off_str = f"{e['offset']:+d}" if e['offset'] != -1 else "adaptive"
        p = f"{pdr(e):.1f} $\\pm$ {pdr_ci(e):.2f}" if e['pdr'] is not None else "--"
        s_ = f"{sf(e):.2f}" if e['avg_sf'] is not None else "--"
        rows_tex.append(
            f"{e['label']} & {e['mode']} & {e['gw']} & "
            f"{e['K']} & {off_str} & {p} & {s_} \\\\"
        )
    rows_tex.append(r"\hline")
    rows_tex.append(r"\end{tabular}")
    rows_tex.append(r"\end{table*}")

    path = os.path.join(TAB_DIR, "table_full_inventory.tex")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows_tex))
    print(f"[TAB] table_full_inventory.tex written")

# ── Run ────────────────────────────────────────────────────────────────────────
print("\n── Generating figures ───────────────────────────────────────────────────")
if ablation_data:
    plot_ablation_bars(ref_data, ablation_data)
if adaptive_data:
    plot_adaptive_attacker(ref_data, adaptive_data)
if gwdensity_data:
    plot_gw_density(ref_data, gwdensity_data)

print("\n── Generating tables ────────────────────────────────────────────────────")
table_ablation(ref_data, ablation_data)
table_adaptive(ref_data, adaptive_data)
table_gw_density(ref_data, gwdensity_data)
table_full_inventory(ref_data, ablation_data, adaptive_data, gwdensity_data)

print("\n── Done ─────────────────────────────────────────────────────────────────")
print(f"Figures → {FIG_DIR}")
print(f"Tables  → {TAB_DIR}")
