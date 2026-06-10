@echo off
REM run_baseline_n1000.bat — Run N=1000 K=0 baseline simulation (5 seeds)
REM Estimated run time: ~80-100 minutes
setlocal
set MSYSTEM=MINGW64
set HOME=C:\omnetpp\
set BASH=C:\omnetpp\tools\win32.x86_64\usr\bin\bash.exe
set LOG=C:\omnet-workspace\scripts\run_baseline_n1000.log
echo START %DATE% %TIME% > "%LOG%"

echo Running N=1000 K=0 baseline simulation...
echo Log: %LOG%

"%BASH%" --login -c "source /c/omnet-workspace/inet4.4/setenv && export INET_ROOT=/c/omnet-workspace/inet4.4 && export PATH=$INET_ROOT/src:$PATH && cd /c/omnet-workspace/flora/simulations && FLO=/c/omnet-workspace/flora/out/clang-release/src/flora && NED=.:../src:$INET_ROOT/src && echo N1K_BASELINE_START >> /c/omnet-workspace/scripts/run_baseline_n1000.log && opp_run -l $FLO -n $NED -u Cmdenv examples/n1000-3gw-k0-baseline.ini >> /c/omnet-workspace/scripts/run_baseline_n1000.log 2>&1 && echo N1K_BASELINE_DONE >> /c/omnet-workspace/scripts/run_baseline_n1000.log"

if errorlevel 1 (
    echo SIMULATION FAILED - check %LOG% for details
) else (
    echo DONE - now run: python scripts/analyze_results.py --export
)
endlocal
