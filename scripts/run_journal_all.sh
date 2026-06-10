#!/bin/bash
# run_journal_all.sh — Run all journal-extension simulation configs
# Usage: bash run_journal_all.sh [optional_stem_filter]
#
# Total: 12 configs, ~100 runs, estimated 3–6 hours

source /c/omnet-workspace/inet4.4/setenv
cd /c/omnet-workspace/flora/simulations
export INET_ROOT=/c/omnet-workspace/inet4.4
export PATH=$INET_ROOT/src:$PATH

LOG_DIR="/c/omnet-workspace/results/run_logs"
mkdir -p "$LOG_DIR"

FILTER="${1:-}"   # optional partial match filter

OK=0
FAIL=0
FAIL_LIST=""

run_config() {
    local stem="$1"
    local desc="$2"

    # Apply filter
    if [ -n "$FILTER" ] && [[ "$stem" != *"$FILTER"* ]]; then
        return 0
    fi

    local ini="examples/${stem}.ini"
    if [ ! -f "$ini" ]; then
        echo "[SKIP] $ini not found"
        return 0
    fi

    echo ""
    echo "============================================================"
    echo "  $desc"
    echo "  INI: $ini"
    echo "  $(date)"
    echo "============================================================"

    local log="$LOG_DIR/${stem}.log"
    opp_run \
        -l ../out/clang-release/src/flora \
        -n .:../src:$INET_ROOT/src \
        -u Cmdenv \
        "$ini" \
        2>&1 | tee "$log"

    local exit_code="${PIPESTATUS[0]}"
    if [ "$exit_code" -eq 0 ]; then
        echo "[OK] $stem completed at $(date)"
        OK=$((OK + 1))
    else
        echo "[FAIL] $stem exited with code $exit_code"
        FAIL=$((FAIL + 1))
        FAIL_LIST="$FAIL_LIST $stem"
    fi
}

echo "======================================================"
echo "  ADR-Secure Journal Experiments"
echo "  Start: $(date)"
echo "======================================================"

# ── 1. Ablation study ─────────────────────────────────────────────────────────
run_config "n100-gw3-K1-median-only"  "Ablation: Median-Only K=1"
run_config "n100-gw3-K1-abstain-only" "Ablation: Abstain-Only K=1"

# ── 2. Adaptive attacker ──────────────────────────────────────────────────────
run_config "n100-gw3-K1-adaptive-step-attack"    "Adaptive Step Attacker / No Defense"
run_config "n100-gw3-K1-adaptive-step-defense"   "Adaptive Step Attacker / ADR-Secure"
run_config "n100-gw3-K1-adaptive-random-attack"  "Adaptive Random Attacker / No Defense"
run_config "n100-gw3-K1-adaptive-random-defense" "Adaptive Random Attacker / ADR-Secure"

# ── 3. Gateway density ────────────────────────────────────────────────────────
run_config "n100-gw4-K1-attack"  "4 GWs K=1 Attack (25% Byzantine)"
run_config "n100-gw4-K1-defense" "4 GWs K=1 ADR-Secure Defense"
run_config "n100-gw5-K2-attack"  "5 GWs K=2 Attack (40% Byzantine)"
run_config "n100-gw5-K2-defense" "5 GWs K=2 ADR-Secure Defense"
run_config "n100-gw5-K3-attack"  "5 GWs K=3 Attack (60% Byzantine — beyond BFT)"
run_config "n100-gw5-K3-defense" "5 GWs K=3 Defense (beyond BFT bound)"

echo ""
echo "======================================================"
echo "  DONE — $(date)"
echo "  Succeeded: $OK / $((OK + FAIL)) configs"
if [ -n "$FAIL_LIST" ]; then
    echo "  Failed: $FAIL_LIST"
fi
echo "======================================================"
echo ""
echo "Next: export SCA files and run analysis"
echo "  python /c/omnet-workspace/scripts/journal_analysis.py --export"
