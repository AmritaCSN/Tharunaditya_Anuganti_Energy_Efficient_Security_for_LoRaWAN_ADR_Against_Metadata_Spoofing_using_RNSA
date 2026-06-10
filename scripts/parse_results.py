"""
parse_results.py  — FLoRa simulation result analyser
Usage (single file):  python parse_results.py path/to/scalars.csv [label]
Usage (comparison):   python parse_results.py file1.csv [label1] -- file2.csv [label2] ...

The '--' separator lets you compare multiple scenarios side-by-side.
"""
import csv, statistics, sys, os

# ─── helpers ────────────────────────────────────────────────────────────────

def load_csv(csv_path):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 7 and row[1] == "scalar":
                rows.append(row)
    return rows

def vals(rows, name_f, mod_f=None):
    out = []
    for r in rows:
        if name_f(r[3]) and (mod_f is None or mod_f(r[2])) and r[6] not in ("", "nan", "NaN"):
            out.append(float(r[6]))
    return out

def extract_metrics(rows):
    ns_der   = vals(rows, lambda n: n == "LoRa_NS_DER")
    gw_der   = vals(rows, lambda n: n == "LoRa_GW_DER")
    final_sf = vals(rows, lambda n: n == "finalSF", lambda m: "loRaNodes" in m)
    sent_all = vals(rows, lambda n: n == "LoRa_AppPacketSent:count", lambda m: "loRaNodes" in m)
    retries  = vals(rows, lambda n: n == "numRetry",                  lambda m: "loRaNodes" in m)

    # Energy per packet
    energy_by_mod = {r[2]: float(r[6]) for r in rows if r[3] == "totalEnergyConsumed"          and r[6] not in ("", "nan", "NaN")}
    sent_by_mod   = {r[2]: float(r[6]) for r in rows if r[3] == "LoRa_AppPacketSent:count"     and r[6] not in ("", "nan", "NaN")}
    e_per_pkt = []
    for app_mod, sent in sent_by_mod.items():
        base       = app_mod.rsplit(".", 1)[0]
        energy_mod = base + ".LoRaNic.radio.energyConsumer"
        if energy_mod in energy_by_mod and sent > 0:
            e_per_pkt.append(energy_by_mod[energy_mod] / sent * 1000)

    sf_node = {sf: sum(1 for v in final_sf if v == sf) for sf in range(7, 13)}
    sf_rcv  = {}
    for sf in range(7, 13):
        v = vals(rows, lambda n, s=sf: n == f"counterUniqueReceivedPacketsPerSF SF{s}")
        sf_rcv[sf] = sum(v) if v else 0

    total_sent    = sum(sent_all)
    server_rcv    = sum(vals(rows, lambda n: n == "LoRa_ServerPacketReceived:count"))
    gw_rcv        = sum(vals(rows, lambda n: n == "LoRa_GWPacketReceived:count"))
    collisions    = sum(vals(rows, lambda n: n == "LoRaReceptionCollision:count"))

    return {
        "pdr":         statistics.mean(ns_der) * 100       if ns_der     else None,
        "gw_pdr":      statistics.mean(gw_der) * 100       if gw_der     else None,
        "avg_sf":      statistics.mean(final_sf)           if final_sf   else None,
        "sf12_pct":    (sf_node.get(12, 0) / len(final_sf) * 100) if final_sf else None,
        "avg_energy":  statistics.mean(e_per_pkt)          if e_per_pkt  else None,
        "retry_rate":  (sum(retries) / total_sent * 100)   if total_sent > 0 and retries else None,
        "total_sent":  total_sent,
        "server_rcv":  server_rcv,
        "gw_rcv":      gw_rcv,
        "collisions":  collisions,
        "sf_node":     sf_node,
        "sf_rcv":      sf_rcv,
        "n_nodes":     len(final_sf),
    }

def print_metrics(label, m):
    w = 58
    print("=" * w)
    print(f"  {label}")
    print("=" * w)
    def f(v, fmt): return fmt % v if v is not None else "N/A"
    print(f"  NS PDR (DER):         {f(m['pdr'],        '%.2f%%')}")
    print(f"  GW DER:               {f(m['gw_pdr'],     '%.2f%%')}")
    print(f"  Avg final SF:         {f(m['avg_sf'],      '%.2f')}")
    print(f"  SF12 node share:      {f(m['sf12_pct'],    '%.1f%%')}  ({m['sf_node'].get(12,0)}/{m['n_nodes']} nodes)")
    print(f"  Avg energy/packet:    {f(m['avg_energy'],  '%.4f mJ')}")
    print(f"  Total sent:           {int(m['total_sent'])}")
    print(f"  Server received:      {int(m['server_rcv'])}")
    print(f"  Retransmission rate:  {f(m['retry_rate'],  '%.2f%%')}")
    print(f"  Collisions:           {int(m['collisions'])}")
    print(f"  Final SF distribution:")
    for sf in range(7, 13):
        c   = m['sf_node'].get(sf, 0)
        bar = "#" * min(c, 50)
        print(f"    SF{sf}: {c:4d} nodes  {bar}")
    print("=" * w)

def print_comparison(scenarios):
    """Print a side-by-side comparison table for multiple scenarios."""
    labels = [s[0] for s in scenarios]
    metrics = [s[1] for s in scenarios]
    col_w = max(20, max(len(l) for l in labels) + 2)
    row_w = 22

    def hdr():
        print(f"{'Metric':{row_w}}", end="")
        for l in labels: print(f"  {l:>{col_w}}", end="")
        print()
        print("-" * (row_w + (col_w + 2) * len(labels)))

    def row(name, key, fmt):
        print(f"{name:{row_w}}", end="")
        for m in metrics:
            v = m.get(key)
            cell = (fmt % v) if v is not None else "N/A"
            print(f"  {cell:>{col_w}}", end="")
        print()

    print("\n" + "=" * (row_w + (col_w + 2) * len(labels)))
    print("  SCENARIO COMPARISON")
    print("=" * (row_w + (col_w + 2) * len(labels)))
    hdr()
    row("NS PDR (%)",       "pdr",        "%.2f")
    row("GW DER (%)",       "gw_pdr",     "%.2f")
    row("Avg final SF",     "avg_sf",     "%.2f")
    row("SF12 nodes (%)",   "sf12_pct",   "%.1f")
    row("Energy/pkt (mJ)",  "avg_energy", "%.4f")
    row("Total sent",       "total_sent", "%.0f")
    row("Server rcv",       "server_rcv", "%.0f")
    row("Retry rate (%)",   "retry_rate", "%.2f")
    row("Collisions",       "collisions", "%.0f")
    print("-" * (row_w + (col_w + 2) * len(labels)))

    # SF distribution per scenario
    print("\n  Final SF node distribution:")
    print(f"  {'SF':{row_w-2}}", end="")
    for l in labels: print(f"  {l:>{col_w}}", end="")
    print()
    for sf in range(7, 13):
        print(f"  SF{sf}{'':{row_w-4}}", end="")
        for m in metrics:
            c = m['sf_node'].get(sf, 0)
            n = m['n_nodes']
            cell = f"{c} ({c/n*100:.0f}%)" if n else "N/A"
            print(f"  {cell:>{col_w}}", end="")
        print()
    print("=" * (row_w + (col_w + 2) * len(labels)))

# ─── CLI argument parsing ────────────────────────────────────────────────────

def parse_args(argv):
    """Return list of (label, csv_path) from argv, split on '--'."""
    scenarios = []
    current = []
    for a in argv:
        if a == "--":
            if current: scenarios.append(current); current = []
        else:
            current.append(a)
    if current: scenarios.append(current)

    result = []
    for s in scenarios:
        if not s: continue
        path = s[0]
        label = s[1] if len(s) > 1 else os.path.basename(path).replace(".csv", "")
        result.append((label, path))
    return result

# ─── main ───────────────────────────────────────────────────────────────────

args = parse_args(sys.argv[1:])

# Default: show week1 baseline if no args given
if not args:
    args = [("n100-gw1 Baseline (week1)", r"C:\omnet-workspace\results\week1_baseline_scalars.csv")]

loaded = []
for label, path in args:
    rows = load_csv(path)
    m = extract_metrics(rows)
    loaded.append((label, m))

if len(loaded) == 1:
    print_metrics(loaded[0][0], loaded[0][1])
else:
    for label, m in loaded:
        print_metrics(label, m)
    print_comparison(loaded)
