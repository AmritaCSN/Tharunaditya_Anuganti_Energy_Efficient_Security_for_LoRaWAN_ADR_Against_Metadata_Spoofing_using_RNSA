#!/bin/bash
source /c/omnet-workspace/inet4.4/setenv
export INET_ROOT=/c/omnet-workspace/inet4.4
export PATH=$INET_ROOT/src:$PATH
cd /c/omnet-workspace/flora/simulations
LOG=/c/omnet-workspace/scripts/run_new_sims.log
echo "=== Simulation start $(date) ===" | tee $LOG
echo "Running corrected 4GW attack..." | tee -a $LOG
opp_run -l /c/omnet-workspace/flora/out/clang-release/src/flora \
  -n .:../src:/c/omnet-workspace/inet4.4/src \
  -u Cmdenv \
  examples/n100-gw4-K1-attack.ini 2>&1 | tee -a $LOG
echo "=== 4GW attack done $(date) ===" | tee -a $LOG
echo "Running corrected 4GW defense..." | tee -a $LOG
opp_run -l /c/omnet-workspace/flora/out/clang-release/src/flora \
  -n .:../src:/c/omnet-workspace/inet4.4/src \
  -u Cmdenv \
  examples/n100-gw4-K1-defense.ini 2>&1 | tee -a $LOG
echo "=== 4GW defense done $(date) ===" | tee -a $LOG
echo "Running N=1000 attack..." | tee -a $LOG
opp_run -l /c/omnet-workspace/flora/out/clang-release/src/flora \
  -n .:../src:/c/omnet-workspace/inet4.4/src \
  -u Cmdenv \
  examples/n1000-3gw-K1-attack.ini 2>&1 | tee -a $LOG
echo "=== N=1000 attack done $(date) ===" | tee -a $LOG
echo "Running N=1000 defense..." | tee -a $LOG
opp_run -l /c/omnet-workspace/flora/out/clang-release/src/flora \
  -n .:../src:/c/omnet-workspace/inet4.4/src \
  -u Cmdenv \
  examples/n1000-3gw-K1-defense.ini 2>&1 | tee -a $LOG
echo "=== ALL DONE $(date) ===" | tee -a $LOG
