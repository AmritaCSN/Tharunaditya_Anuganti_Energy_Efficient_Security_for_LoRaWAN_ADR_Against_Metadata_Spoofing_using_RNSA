#!/usr/bin/env pwsh
# run_new_sims.ps1 — Run all new simulation configs (N=200, N=500, uniform).
# Usage:  .\scripts\run_new_sims.ps1 [-SkipExisting]

param([switch]$SkipExisting)

$ROOT    = "C:\omnet-workspace"
$SCA_DIR = "$ROOT\flora\simulations\results"

# Config → max run index (inclusive)
$jobs = [ordered]@{
    "n200-3gw-k0-baseline"  = 4    # 5 reps, no iterations
    "n200-3gw-K1-attack"    = 9    # 2 offsets x 5 reps
    "n200-3gw-K1-defense"   = 9
    "n500-3gw-k0-baseline"  = 4
    "n500-3gw-K1-attack"    = 9
    "n500-3gw-K1-defense"   = 9
    "n100-3gw-uniform"      = 19   # 2 offsets x 2 adrMethods x 5 reps
}

$totalRuns = ($jobs.Values | Measure-Object -Sum).Sum + $jobs.Count  # sum of (maxRun+1)
$done = 0
$startTime = Get-Date

Write-Host "=== New Simulations Batch ===" -ForegroundColor Cyan
Write-Host "Total runs: $totalRuns"
Write-Host "Started   : $startTime"
Write-Host ""

foreach ($cfg in $jobs.Keys) {
    $maxRun = $jobs[$cfg]
    for ($r = 0; $r -le $maxRun; $r++) {
        $scaFile = "$SCA_DIR\$cfg-s$r.ini.sca"
        if ($SkipExisting -and (Test-Path $scaFile)) {
            Write-Host "[SKIP] $cfg run $r" -ForegroundColor DarkGray
            $done++
            continue
        }
        $elapsed = (Get-Date) - $startTime
        Write-Host "[$($done+1)/$totalRuns] $cfg run $r  (elapsed $($elapsed.ToString('hh\:mm\:ss')))" -ForegroundColor Yellow

        & "$ROOT\run_project.ps1" -Config $cfg -Run $r

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ERROR exit $LASTEXITCODE" -ForegroundColor Red
        } else {
            if (Test-Path $scaFile) {
                $sz = [math]::Round((Get-Item $scaFile).Length/1KB, 1)
                Write-Host "  OK ($sz KB)" -ForegroundColor Green
            } else {
                Write-Host "  WARN: .sca file not found at $scaFile" -ForegroundColor Magenta
            }
        }
        $done++
    }
}

$total = (Get-Date) - $startTime
Write-Host ""
Write-Host "=== BATCH COMPLETE ===" -ForegroundColor Cyan
Write-Host "Elapsed: $($total.ToString('hh\:mm\:ss'))"
Write-Host "Runs   : $done / $totalRuns"

# Quick summary
Write-Host ""
Write-Host "--- SCA file check ---"
foreach ($cfg in $jobs.Keys) {
    $maxRun = $jobs[$cfg]
    $found = (Get-ChildItem "$SCA_DIR\$cfg-s*.sca" -ErrorAction SilentlyContinue).Count
    $expected = $maxRun + 1
    $status = if ($found -eq $expected) { "OK" } else { "MISSING $($expected - $found)" }
    Write-Host "  $cfg : $found / $expected  [$status]"
}
