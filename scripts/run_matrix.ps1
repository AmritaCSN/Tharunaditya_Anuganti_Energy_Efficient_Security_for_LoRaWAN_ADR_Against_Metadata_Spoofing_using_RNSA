#!/usr/bin/env pwsh
# run_matrix.ps1 — Run the full ADR-Secure experiment matrix.
#
# Configs run (10 runs each = 5 reps x 2 offsets -20/-40 dB):
#   n100-gw2-defense     : K=1 malicious, ADR-Secure (direct pair for existing gw2-attack)
#   n100-gw3-K1-attack   : 3 GWs, K=1 malicious, ADR-Baseline
#   n100-gw3-K1-defense  : 3 GWs, K=1 malicious, ADR-Secure
#   n100-gw3-K2-attack   : 3 GWs, K=2 malicious, ADR-Baseline
#   n100-gw3-K2-defense  : 3 GWs, K=2 malicious, ADR-Secure
#
# Usage:
#   .\scripts\run_matrix.ps1                    # run all configs
#   .\scripts\run_matrix.ps1 -Configs "n100-gw2-defense","n100-gw3-K1-attack"
#   .\scripts\run_matrix.ps1 -SkipExisting      # skip runs whose .sca already exists

param(
    [string[]]$Configs = @(
        "n100-gw2-defense",
        "n100-gw3-K1-attack",
        "n100-gw3-K1-defense",
        "n100-gw3-K2-attack",
        "n100-gw3-K2-defense",
        "n200-3gw-k0-baseline",
        "n200-3gw-K1-attack",
        "n200-3gw-K1-defense",
        "n500-3gw-k0-baseline",
        "n500-3gw-K1-attack",
        "n500-3gw-K1-defense"
    ),
    [switch]$SkipExisting
)

$ROOT      = "C:\omnet-workspace"
$SCA_DIR   = "$ROOT\flora\simulations\results"
$LOG_DIR   = "$ROOT\results"

$totalRuns  = $Configs.Count * 10
$doneCount  = 0
$startTime  = Get-Date

Write-Host "=== ADR-Secure Experiment Matrix ===" -ForegroundColor Cyan
Write-Host "Configs : $($Configs -join ', ')"
Write-Host "Runs    : $totalRuns total (10 per config)"
Write-Host "Started : $startTime"
Write-Host ""

foreach ($cfg in $Configs) {
    for ($r = 0; $r -le 9; $r++) {
        $scaFile = "$SCA_DIR\$cfg-s$r.ini.sca"
        if ($SkipExisting -and (Test-Path $scaFile)) {
            Write-Host "[SKIP] $cfg run $r — already exists" -ForegroundColor DarkGray
            $doneCount++
            continue
        }

        $elapsed = (Get-Date) - $startTime
        Write-Host "[$($doneCount+1)/$totalRuns] $cfg run $r  (elapsed: $($elapsed.ToString('hh\:mm\:ss')))" -ForegroundColor Yellow

        & "$ROOT\run_project.ps1" -Config $cfg -Run $r

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ERROR: run_project.ps1 returned $LASTEXITCODE for $cfg run $r" -ForegroundColor Red
        } else {
            $sz = if (Test-Path $scaFile) { [math]::Round((Get-Item $scaFile).Length/1MB, 2) } else { "MISSING" }
            Write-Host "  OK  — $scaFile  ($sz MB)" -ForegroundColor Green
        }
        $doneCount++
    }
}

$totalTime = (Get-Date) - $startTime
Write-Host ""
Write-Host "=== ALL MATRIX RUNS COMPLETE ===" -ForegroundColor Cyan
Write-Host "Total time : $($totalTime.ToString('hh\:mm\:ss'))"
Write-Host "Completed  : $doneCount / $totalRuns"
