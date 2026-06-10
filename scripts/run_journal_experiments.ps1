#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run all journal-extension simulation experiments.

.DESCRIPTION
    Executes the 12 new INI configs in sequence via opp_run (Cmdenv).
    Each INI has repeat=5 and an attackOffset sweep {20, 40} where applicable,
    giving 10 runs per config (5 for adaptive/ablation configs with no sweep).

    Total new runs: ~100
    Estimated wall time: 3–5 hours (depends on machine)

.PARAMETER DryRun
    Print commands without executing.

.PARAMETER Config
    Run a single config by stem name (partial match).

.EXAMPLE
    .\scripts\run_journal_experiments.ps1
    .\scripts\run_journal_experiments.ps1 -DryRun
    .\scripts\run_journal_experiments.ps1 -Config "ablation"
#>
param(
    [switch]$DryRun,
    [string]$Config = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Environment ──────────────────────────────────────────────────────────────
$env:HOME    = "C:\omnetpp\"
$env:MSYSTEM = "MINGW64"
$BASH = "C:\omnetpp\tools\win32.x86_64\usr\bin\bash.exe"

$FLORA_DIR   = "C:\omnet-workspace\flora"
$SIM_DIR     = "$FLORA_DIR\simulations"
$EXE         = "$FLORA_DIR\out\clang-release\src\flora"
$INET_NED    = "C:\omnet-workspace\inet4.4\src"
$FLORA_NED   = "$FLORA_DIR\src;$SIM_DIR"
$NED_PATH    = "${INET_NED};${FLORA_NED}"
$LOG_DIR     = "C:\omnet-workspace\results\run_logs"

New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

# ── Config registry ───────────────────────────────────────────────────────────
# (ini_stem, description, has_offset_sweep)
$CONFIGS = @(
    # ── Ablation study ────────────────────────────────────────────────────
    @{ stem="n100-gw3-K1-median-only";    desc="Ablation: Median-Only K=1";   sweep=$true  },
    @{ stem="n100-gw3-K1-abstain-only";   desc="Ablation: Abstain-Only K=1";  sweep=$true  },
    # ── Adaptive attacker ─────────────────────────────────────────────────
    @{ stem="n100-gw3-K1-adaptive-step-attack";    desc="Adaptive Step / No Defense";  sweep=$false },
    @{ stem="n100-gw3-K1-adaptive-step-defense";   desc="Adaptive Step / ADR-Secure";  sweep=$false },
    @{ stem="n100-gw3-K1-adaptive-random-attack";  desc="Adaptive Random / No Defense";sweep=$false },
    @{ stem="n100-gw3-K1-adaptive-random-defense"; desc="Adaptive Random / ADR-Secure";sweep=$false },
    # ── Gateway density ───────────────────────────────────────────────────
    @{ stem="n100-gw4-K1-attack";   desc="4GW K=1 Attack";   sweep=$true },
    @{ stem="n100-gw4-K1-defense";  desc="4GW K=1 Defense";  sweep=$true },
    @{ stem="n100-gw5-K2-attack";   desc="5GW K=2 Attack";   sweep=$true },
    @{ stem="n100-gw5-K2-defense";  desc="5GW K=2 Defense";  sweep=$true },
    @{ stem="n100-gw5-K3-attack";   desc="5GW K=3 Attack";   sweep=$true },
    @{ stem="n100-gw5-K3-defense";  desc="5GW K=3 Defense";  sweep=$true }
)

# Filter by -Config flag
if ($Config -ne "") {
    $CONFIGS = $CONFIGS | Where-Object { $_.stem -like "*$Config*" }
    if ($CONFIGS.Count -eq 0) {
        Write-Error "No configs matched '$Config'"
        exit 1
    }
}

# ── opp_run helper ────────────────────────────────────────────────────────────
function Invoke-OppRun {
    param([string]$IniFile, [string]$Stem, [string]$Desc, [bool]$Sweep)

    $nRuns = if ($Sweep) { 10 } else { 5 }
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host " $Desc" -ForegroundColor Cyan
    Write-Host " INI : $IniFile" -ForegroundColor Cyan
    Write-Host " Runs: 0..$($nRuns - 1)" -ForegroundColor Cyan
    Write-Host "=====================================================" -ForegroundColor Cyan

    $logFile = "$LOG_DIR\${Stem}.log"

    # Build opp_run command (relative paths from flora/simulations, matching run_project.ps1)
    $IniPosix = $IniFile -replace '\\','/' -replace 'C:','/c'
    $oppCmd = @"
source /c/omnet-workspace/inet4.4/setenv
cd /c/omnet-workspace/flora/simulations
export INET_ROOT=/c/omnet-workspace/inet4.4
opp_run \
  -l ../out/clang-release/src/flora \
  -n .:`$INET_ROOT/src:../src \
  -u Cmdenv \
  "$IniPosix" \
  2>&1 | tee /c/omnet-workspace/results/run_logs/${Stem}.log
"@

    if ($DryRun) {
        Write-Host "[DRY RUN] bash --login -c `"$oppCmd`"" -ForegroundColor Yellow
        return $true
    }

    $startTime = Get-Date
    $proc = & $BASH --login -c $oppCmd
    $exitCode = $LASTEXITCODE
    $elapsed  = (Get-Date) - $startTime

    if ($exitCode -eq 0) {
        Write-Host "  [OK]  Completed in $($elapsed.ToString('hh\:mm\:ss'))" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  [FAIL] Exit $exitCode after $($elapsed.ToString('hh\:mm\:ss'))" -ForegroundColor Red
        Write-Host "  Log: $logFile" -ForegroundColor Yellow
        return $false
    }
}

# ── Main loop ─────────────────────────────────────────────────────────────────
$total   = $CONFIGS.Count
$success = 0
$failed  = @()
$overall = Get-Date

Write-Host ""
Write-Host "ADR-Secure Journal Experiments" -ForegroundColor White
Write-Host "Running $total scenario configs…" -ForegroundColor White
if ($DryRun) { Write-Host "[DRY-RUN MODE]" -ForegroundColor Yellow }

foreach ($cfg in $CONFIGS) {
    $iniPath = "$SIM_DIR\examples\$($cfg.stem).ini"
    if (-not (Test-Path $iniPath)) {
        Write-Host "  [SKIP] INI not found: $iniPath" -ForegroundColor Yellow
        continue
    }
    $ok = Invoke-OppRun -IniFile $iniPath -Stem $cfg.stem `
                        -Desc $cfg.desc -Sweep $cfg.sweep
    if ($ok) { $success++ } else { $failed += $cfg.stem }
}

$elapsed = (Get-Date) - $overall
Write-Host ""
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor White
Write-Host "  Completed : $success / $total configs" -ForegroundColor White
Write-Host "  Elapsed   : $($elapsed.ToString('hh\:mm\:ss'))" -ForegroundColor White
if ($failed.Count -gt 0) {
    Write-Host "  Failed    : $($failed -join ', ')" -ForegroundColor Red
}
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor White
Write-Host ""
Write-Host "Next step: export results and run analysis:" -ForegroundColor Cyan
Write-Host "  python scripts/journal_analysis.py --export" -ForegroundColor Cyan
