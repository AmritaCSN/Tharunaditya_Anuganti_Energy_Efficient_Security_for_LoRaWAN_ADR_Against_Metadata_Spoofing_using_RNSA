# run_all.ps1 — Complete ADR-Secure journal pipeline
# Runs N=1000 baseline simulation (if not done), exports all CSVs,
# regenerates all figures and tables, and reports status.
#
# Usage: .\scripts\run_all.ps1
# Log:   scripts\run_all.log

$ErrorActionPreference = "Stop"
$LogFile  = "C:\omnet-workspace\scripts\run_all.log"
$SCA_DIR  = "C:\omnet-workspace\flora\simulations\results"
$BASH     = "C:\omnetpp\tools\win32.x86_64\usr\bin\bash.exe"
$WORKSPACE = "C:\omnet-workspace"

function Write-Log {
    param([string]$msg, [string]$Color = "White")
    $ts   = Get-Date -Format "HH:mm:ss"
    $line = "[$ts] $msg"
    Write-Host $line -ForegroundColor $Color
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

Set-Content -Path $LogFile -Value "=== run_all.ps1 started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" -Encoding UTF8
Set-Location $WORKSPACE

Write-Log "=== ADR-Secure Journal Pipeline ===" "Cyan"
Write-Log "Log file: $LogFile" "Gray"

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1: N=1000 baseline simulation
# ─────────────────────────────────────────────────────────────────────────────
Write-Log "" 
Write-Log "--- Phase 1: N=1000 K=0 Baseline Simulation ---" "Yellow"

$existing = @(Get-ChildItem "$SCA_DIR\n1000-3gw-k0-baseline-s*.ini.sca" -EA SilentlyContinue)
if ($existing.Count -ge 5) {
    Write-Log "Already complete: $($existing.Count)/5 SCA files found. Skipping simulation." "Green"
} else {
    Write-Log "SCA files found so far: $($existing.Count)/5. Starting simulation..." "Yellow"
    Write-Log "Expected duration: ~80-100 minutes. Do NOT close this window." "Yellow"
    Write-Log "Sim started at $(Get-Date -Format 'HH:mm:ss')" "Yellow"

    $env:MSYSTEM = "MINGW64"
    $env:HOME    = "C:\omnetpp\"

    $bashCmd = @"
source /c/omnet-workspace/inet4.4/setenv &&
export INET_ROOT=/c/omnet-workspace/inet4.4 &&
export PATH=`$INET_ROOT/src:`$PATH &&
cd /c/omnet-workspace/flora/simulations &&
FLO=/c/omnet-workspace/flora/out/clang-release/src/flora &&
NED=.:../src:`$INET_ROOT/src &&
echo N1K_BASELINE_START &&
opp_run -l `$FLO -n `$NED -u Cmdenv examples/n1000-3gw-k0-baseline.ini &&
echo N1K_BASELINE_DONE
"@ -replace "`n", " "

    Write-Log "Running: opp_run examples/n1000-3gw-k0-baseline.ini" "Gray"
    & $BASH --login -c $bashCmd 2>&1 | Tee-Object -FilePath $LogFile -Append

    $after = @(Get-ChildItem "$SCA_DIR\n1000-3gw-k0-baseline-s*.ini.sca" -EA SilentlyContinue)
    if ($after.Count -lt 5) {
        Write-Log "ERROR: Simulation produced only $($after.Count)/5 SCA files." "Red"
        Write-Log "Check $LogFile for opp_run output." "Red"
        Write-Host ""
        Write-Host "SIMULATION FAILED. Review the log file and re-run." -ForegroundColor Red
        exit 1
    }
    Write-Log "Simulation done! $($after.Count)/5 SCA files produced. Finished at $(Get-Date -Format 'HH:mm:ss')" "Green"
}

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2: Export CSVs and regenerate conference paper outputs
# ─────────────────────────────────────────────────────────────────────────────
Write-Log ""
Write-Log "--- Phase 2: Export CSVs + Regenerate Conference Outputs ---" "Yellow"

$env:PYTHONUTF8 = "1"
Write-Log "Running: python scripts/analyze_results.py --export" "Gray"
python -u scripts\analyze_results.py --export 2>&1 | Tee-Object -FilePath $LogFile -Append
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Log "ERROR: analyze_results.py exited with code $exitCode" "Red"
    if (Test-Path "$WORKSPACE\results\analyze_error.log") {
        Write-Log "Traceback saved to results\analyze_error.log — review it for the fix." "Red"
        Write-Host ""
        Get-Content "$WORKSPACE\results\analyze_error.log" | Select-Object -Last 20
    }
    Write-Host ""
    Write-Host "Phase 2 FAILED. See above for the Python traceback." -ForegroundColor Red
    exit 1
}
Write-Log "analyze_results.py complete." "Green"

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3: Export CSVs and regenerate journal extension outputs
# ─────────────────────────────────────────────────────────────────────────────
Write-Log ""
Write-Log "--- Phase 3: Export CSVs + Regenerate Journal Outputs ---" "Yellow"

Write-Log "Running: python scripts/journal_analysis.py --export" "Gray"
python -u scripts\journal_analysis.py --export 2>&1 | Tee-Object -FilePath $LogFile -Append
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Log "ERROR: journal_analysis.py exited with code $exitCode" "Red"
    Write-Host "Phase 3 FAILED. See log for details." -ForegroundColor Red
    exit 1
}
Write-Log "journal_analysis.py complete." "Green"

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4: Final status report
# ─────────────────────────────────────────────────────────────────────────────
Write-Log ""
Write-Log "--- Phase 4: Final Verification ---" "Yellow"

$csvFiles = @(Get-ChildItem "$WORKSPACE\results\*.csv" -EA SilentlyContinue)
$figFiles = @(Get-ChildItem "$WORKSPACE\results\figures\*.pdf" -EA SilentlyContinue)
$tabFiles = @(Get-ChildItem "$WORKSPACE\results\tables\*.tex" -EA SilentlyContinue)

Write-Log "CSVs in results/:    $($csvFiles.Count)" "Cyan"
Write-Log "Figures (PDF):       $($figFiles.Count)" "Cyan"
Write-Log "LaTeX tables:        $($tabFiles.Count)" "Cyan"

# Check scalability table for the key cell
$scalTab = "$WORKSPACE\results\tables\table6_scalability.tex"
if (Test-Path $scalTab) {
    $content = Get-Content $scalTab -Raw
    if ($content -match "Baseline.*---") {
        Write-Log "WARNING: table6_scalability still has '---' for N=1000 baseline!" "Red"
    } else {
        Write-Log "table6_scalability.tex: N=1000 baseline cell is filled." "Green"
    }
}

# List all generated figures
Write-Log ""
Write-Log "Generated figures:" "Cyan"
foreach ($f in $figFiles | Sort-Object Name) {
    Write-Log "  $($f.Name)  ($([int]($f.Length/1KB)) KB)" "Gray"
}

Write-Log ""
Write-Log "=== ALL DONE at $(Get-Date -Format 'HH:mm:ss') ===" "Green"
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Pipeline complete! See log: $LogFile" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
