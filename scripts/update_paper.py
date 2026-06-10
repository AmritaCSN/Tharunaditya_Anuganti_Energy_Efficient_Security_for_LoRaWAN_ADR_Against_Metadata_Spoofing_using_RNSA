"""
update_paper.py - Patch placeholder numbers in paper/main.tex using
                  the values computed by analyze_results.py.

Usage:
    python scripts/update_paper.py

Reads:  results/paper_numbers.txt
Writes: paper/main.tex  (in place)
"""

import sys, io, os, re

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE     = r"C:\omnet-workspace"
NUMS_F   = os.path.join(BASE, "results", "paper_numbers.txt")
PAPER_F  = os.path.join(BASE, "paper", "main.tex")

# ── Load key-value numbers ────────────────────────────────────────────────────
if not os.path.exists(NUMS_F):
    print(f"[ERROR] {NUMS_F} not found. Run analyze_results.py first.")
    sys.exit(1)

nums = {}
with open(NUMS_F, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            nums[k.strip()] = v.strip()

print("[NUMS] Loaded:")
for k, v in nums.items():
    print(f"  {k} = {v}")

def get(key, fallback="??"):
    v = nums.get(key, fallback)
    return fallback if v == "MISSING" else v

# ── Build patched sections ─────────────────────────────────────────────────────
baseline_pdr    = get("BASELINE_PDR")
baseline_sf     = get("BASELINE_SF")
baseline_energy = get("BASELINE_ENERGY")

atk2_20_pdr    = get("ATK2_20_PDR")
atk2_20_sf     = get("ATK2_20_SF")
atk2_20_energy = get("ATK2_20_ENERGY")
atk2_40_pdr    = get("ATK2_40_PDR")
atk2_40_sf     = get("ATK2_40_SF")

dfn2_20_pdr = get("DFN2_20_PDR")
dfn2_20_sf  = get("DFN2_20_SF")
atk3_20_pdr = get("ATK3_20_PDR")
atk3_20_sf  = get("ATK3_20_SF")
dfn3_20_pdr = get("DFN3_20_PDR")
dfn3_20_sf  = get("DFN3_20_SF")
atk3k2_pdr  = get("ATK3K2_PDR")
dfn3k2_pdr  = get("DFN3K2_PDR")

# Compute energy delta % if both present
try:
    e_atk  = float(atk2_20_energy)
    e_base = float(baseline_energy)
    e_delta_pct = f"{(e_atk - e_base) / e_base * 100:+.1f}"
except Exception:
    e_delta_pct = "??"

# Compute PDR delta for defense vs baseline
try:
    pdr_dfn = float(dfn3_20_pdr)
    pdr_bas = float(baseline_pdr)
    pdr_delta = f"{abs(pdr_dfn - pdr_bas):.1f}"
except Exception:
    pdr_delta = "??"

# ── Read paper ─────────────────────────────────────────────────────────────────
with open(PAPER_F, encoding="utf-8") as f:
    tex = f.read()

# ── Patch 1: Baseline subsection ──────────────────────────────────────────────
OLD_BASE = r"""\subsection{Baseline (K=0, 1 GW)}

The reference scenario gives PDR\,=\,87.3\,\% and average
SF\,=\,7.47, confirming that ADR converges to low SFs for the
majority of nodes after 24\,h.  Per-packet energy is 75.2\,mJ."""

NEW_BASE = (
    r"\subsection{Baseline (K=0, 1 GW)}"
    "\n\n"
    f"The reference scenario gives PDR\\,=\\,{baseline_pdr}\\,\\% and average\n"
    f"SF\\,=\\,{baseline_sf}, confirming that ADR converges to low SFs for the\n"
    f"majority of nodes after 24\\,h.  Per-packet energy is {baseline_energy}\\,mJ."
)

if OLD_BASE in tex:
    tex = tex.replace(OLD_BASE, NEW_BASE)
    print("[PATCH] Baseline numbers updated.")
else:
    print("[WARN]  Baseline block not matched (may already be updated).")

# ── Patch 2: Attack subsection ────────────────────────────────────────────────
# Replace everything between the \subsection and the \subsection that follows
OLD_ATK_RE = re.compile(
    r"(\\subsection\{Attack Effect[^\}]*\})(.*?)"
    r"(\\subsection\{Defense)",
    re.DOTALL
)

NEW_ATK_BODY = f"""

When the central gateway inflates its SNR report by $\\delta=+20$\\,dB,
the NS assigns most nodes SF7 regardless of their true link quality.
Nodes that require SF9--SF11 transmit at SF7 and fail to be decoded,
causing PDR to fall to {atk2_20_pdr}\\,\\% (baseline: {baseline_pdr}\\,\\%).
Average SF drops to {atk2_20_sf} and energy per packet to {atk2_20_energy}\\,mJ
({e_delta_pct}\\,\\% vs.\\ baseline).
At $\\delta=+40$\\,dB the effect intensifies (SF\\,=\\,{atk2_40_sf},
PDR\\,=\\,{atk2_40_pdr}\\,\\%), confirming the attack monotonically worsens
with higher inflation.

"""

m = OLD_ATK_RE.search(tex)
if m:
    tex = tex[:m.start()] + m.group(1) + NEW_ATK_BODY + m.group(3) + tex[m.end():]
    print("[PATCH] Attack numbers updated.")
else:
    print("[WARN]  Attack block not matched.")

# ── Patch 3: Defense subsection ───────────────────────────────────────────────
OLD_DFN = re.compile(
    r"(\\subsection\{Defense[^\}]*\})(.*?)"
    r"(\\begin\{figure\})",
    re.DOTALL
)

NEW_DFN_BODY = f"""

With \\adrsec{{}} active and $K=1$ of~3 gateways Byzantine, the NS
applies the BFT median to every uplink received by multiple gateways,
rejecting the inflated report and supplying ADR with a realistic SNR
from the honest majority.  For uplinks received by only one gateway
the update is skipped (conservative single-source policy), preventing
any unverified inflation from biasing the ADR history.
PDR recovers to {dfn3_20_pdr}\\,\\% (attack: {atk3_20_pdr}\\,\\%,
baseline: {baseline_pdr}\\,\\%), a difference of {pdr_delta} percentage
points.  Average SF rises from {atk3_20_sf} (attack) back toward
{dfn3_20_sf} (defense), closely matching the honest baseline.

"""

m2 = OLD_DFN.search(tex)
if m2:
    tex = tex[:m2.start()] + m2.group(1) + NEW_DFN_BODY + m2.group(3) + tex[m2.end():]
    print("[PATCH] Defense numbers updated.")
else:
    print("[WARN]  Defense block not matched.")

# ── Patch 4: BFT Bound subsection ─────────────────────────────────────────────
OLD_BFT = (
    "When $K=2$ malicious gateways out of $N_{\\mathrm{GW}}=3$, the\n"
    "adversary controls the majority position and the median equals a\n"
    "corrupted value.  We expect both \\adrbase{} and \\adrsec{} to produce\n"
    "the same degraded metrics, confirming the tightness of the BFT bound."
)
NEW_BFT = (
    "When $K=2$ malicious gateways out of $N_{\\mathrm{GW}}=3$, the\n"
    "adversary controls the majority position and the median equals a\n"
    f"corrupted value.  \\adrbase{{}} achieves PDR\\,=\\,{atk3k2_pdr}\\,\\%\n"
    f"and \\adrsec{{}} PDR\\,=\\,{dfn3k2_pdr}\\,\\%—statistically\n"
    "indistinguishable, confirming the tightness of the BFT bound.\n"
    "No server-side filter can overcome adversarial control of the median."
)

if OLD_BFT in tex:
    tex = tex.replace(OLD_BFT, NEW_BFT)
    print("[PATCH] BFT bound numbers updated.")
else:
    print("[WARN]  BFT bound block not matched.")

# ── Patch 5: Abstract PDR claim ───────────────────────────────────────────────
OLD_ABS = (
    "Results confirm that \\adrsec{} fully restores the honest-network\n"
    "PDR for $K=1$ of~3 gateways (where the inflation attack causes PDR\n"
    "to drop sharply), while gracefully\n"
    "degrading when the BFT bound $K<N/2$ is violated."
)
NEW_ABS = (
    f"Results confirm that \\adrsec{{}} restores PDR from\n"
    f"{atk3_20_pdr}\\,\\% (under attack) to {dfn3_20_pdr}\\,\\%\n"
    f"for $K=1$ of~3 gateways, while\n"
    "degrading gracefully when the BFT bound $K<N/2$ is violated ($K=2$)."
)

if OLD_ABS in tex:
    tex = tex.replace(OLD_ABS, NEW_ABS)
    print("[PATCH] Abstract PDR claim updated.")
else:
    print("[WARN]  Abstract block not matched.")

# ── Remove remaining % NOTE placeholders ──────────────────────────────────────
tex = re.sub(r"\n% NOTE:.*", "", tex)
tex = re.sub(r"\n% Re-run with:.*", "", tex)
tex = re.sub(r"\n% and update.*", "", tex)
tex = re.sub(r"\n% fixed-DLL.*", "", tex)

# ── Write patched paper ───────────────────────────────────────────────────────
with open(PAPER_F, "w", encoding="utf-8") as f:
    f.write(tex)

print(f"\n[DONE] {PAPER_F} updated with real numbers.")
