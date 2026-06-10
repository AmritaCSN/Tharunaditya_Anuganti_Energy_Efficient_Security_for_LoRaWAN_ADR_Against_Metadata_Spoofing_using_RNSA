#!/bin/bash
# run_new_sims.sh — Run corrected 4GW and new N=1000 simulations
# Corrected 4GW: malicious GW now at cluster centre (544,544)
# N=1000: scalability study extension
#
# Usage: bash scripts/run_new_sims.sh
# Estimated time: ~3-4 hours total (40 runs × 24h sim-time, parallelised)

set -e
cd "$(dirname "$0")/../flora/simulations"

source /c/omnet-workspace/inet4.4/setenv
export INET_ROOT=/c/omnet-workspace/inet4.4
export PATH=$INET_ROOT/src:$PATH

FLORA_LIB="/c/omnet-workspace/flora/out/clang-release/src/flora"
NED_PATH=".:../src:$INET_ROOT/src"

run_ini() {
    local ini="$1"
    local label="$2"
    echo "=== Running: $label ==="
    opp_run -l "$FLORA_LIB" -n "$NED_PATH" -u Cmdenv "$ini"
    echo "=== Done: $label ==="
}

echo "================================================================"
echo " Starting new simulation campaigns — $(date)"
echo "================================================================"

# ── 1. Corrected 4GW K=1 (20 runs total: 10 per config × 2 offsets) ──────────
run_ini examples/n100-gw4-K1-attack.ini   "4GW K=1 Attack   (corrected, 20 runs)"
run_ini examples/n100-gw4-K1-defense.ini  "4GW K=1 Defense  (corrected, 20 runs)"

# ── 2. N=1000 scalability (20 runs total) ────────────────────────────────────
run_ini examples/n1000-3gw-K1-attack.ini  "N=1000 Attack    (10 runs)"
run_ini examples/n1000-3gw-K1-defense.ini "N=1000 Defense   (10 runs)"

echo "================================================================"
echo " ALL DONE — $(date)"
echo "================================================================"
