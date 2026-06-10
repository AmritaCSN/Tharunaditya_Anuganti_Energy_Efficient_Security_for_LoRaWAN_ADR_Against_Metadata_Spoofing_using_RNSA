
# scripts/verify_build.ps1
# Post-build verification script for OMNeT++ + INET + FLoRa
# Run after building all components to confirm success.

param(
    [string]$OmnetRoot = "C:\omnetpp",
    [string]$SamplesDir = "C:\omnetpp\samples",
    [string]$InetDir = "C:\omnetpp\samples\inet4.4",
    [string]$FloraDir = "C:\omnetpp\samples\flora"
)

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Build Verification: OMNeT++ + INET + FLoRa" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

$pass = 0
$fail = 0

function Test-FileAndReport([string]$path, [string]$label) {
    if (Test-Path $path) {
        Write-Host "  [OK] $label" -ForegroundColor Green
        $script:pass++
        return $true
    } else {
        Write-Host "  [MISSING] $label" -ForegroundColor Red
        Write-Host "            Path: $path" -ForegroundColor DarkRed
        $script:fail++
        return $false
    }
}

function Section([string]$t) {
    Write-Host ""
    Write-Host "── $t" -ForegroundColor Cyan
}

# ─── OMNeT++ ─────────────────────────────────────────────────────────────────
Section "OMNeT++ 6.0.3 Build Outputs"

Test-FileAndReport "$OmnetRoot\bin\opp_run.exe"         "opp_run.exe (main simulator runner)"
Test-FileAndReport "$OmnetRoot\bin\opp_makemake.exe"    "opp_makemake.exe (build system)"
Test-FileAndReport "$OmnetRoot\bin\opp_scavetool.exe"   "opp_scavetool.exe (results export)"
Test-FileAndReport "$OmnetRoot\bin\opp_runall.exe"      "opp_runall.exe (parallel runs)"
Test-FileAndReport "$OmnetRoot\ide\omnetpp.exe"         "omnetpp.exe (IDE)"
Test-FileAndReport "$OmnetRoot\lib\liboppenvir.dll"     "liboppenvir.dll (or .a)"

# ─── INET ─────────────────────────────────────────────────────────────────────
Section "INET 4.4.1 Build Outputs"

# Try both release and debug
$inetBuilt = $false
$inetDlls = @(
    "$InetDir\out\gcc-release\src\INET.dll",
    "$InetDir\out\gcc-release\src\libINET.dll",
    "$InetDir\out\gcc-debug\src\INET_dbg.dll",
    "$InetDir\out\clang-release\src\INET.dll"
)

foreach ($dll in $inetDlls) {
    if (Test-Path $dll) {
        Write-Host "  [OK] INET library: $(Split-Path $dll -Leaf)" -ForegroundColor Green
        Write-Host "       Path: $dll" -ForegroundColor DarkGray
        $pass++
        $inetBuilt = $true
        break
    }
}

if (-not $inetBuilt) {
    Write-Host "  [MISSING] INET library (INET.dll or INET_dbg.dll)" -ForegroundColor Red
    Write-Host "            Expected in: $InetDir\out\" -ForegroundColor DarkRed
    Write-Host "            Fix: Import INET into IDE → Build Project" -ForegroundColor Yellow
    $fail++
}

# Check INET NED files compiled
$nedCpp = Get-ChildItem -Path "$InetDir\out" -Filter "*.o" -Recurse -ErrorAction SilentlyContinue
if ($nedCpp -and $nedCpp.Count -gt 100) {
    Write-Host "  [OK] INET object files found ($($nedCpp.Count) .o files)" -ForegroundColor Green
    $pass++
} elseif ($nedCpp) {
    Write-Host "  [WARN] Only $($nedCpp.Count) .o files — INET may be partially built" -ForegroundColor Yellow
} else {
    Write-Host "  [MISSING] No INET build output found" -ForegroundColor Red
    $fail++
}

# ─── FLoRa ────────────────────────────────────────────────────────────────────
Section "FLoRa 1.1.0 Build Outputs"

# Check for flora executable
$floraExePaths = @(
    "$FloraDir\src\flora.exe",
    "$FloraDir\out\gcc-release\src\flora.exe",
    "$FloraDir\out\gcc-debug\src\flora.exe"
)

$floraBuilt = $false
foreach ($exe in $floraExePaths) {
    if (Test-Path $exe) {
        $size = [math]::Round((Get-Item $exe).Length / 1MB, 1)
        Write-Host "  [OK] flora.exe found: $exe ($size MB)" -ForegroundColor Green
        $pass++
        $floraBuilt = $true
        break
    }
}

if (-not $floraBuilt) {
    Write-Host "  [MISSING] flora.exe not found" -ForegroundColor Red
    Write-Host "            Fix: Set Project References to inet4.4 → Build flora project" -ForegroundColor Yellow
    $fail++
}

# Check simulation files
Section "Simulation Files"

$simFiles = @(
    @{ Path = "$FloraDir\simulations\omnetpp.ini";                    Label = "Default simulation (omnetpp.ini)" },
    @{ Path = "$FloraDir\simulations\package.ned";                    Label = "NED package declaration" },
    @{ Path = "$FloraDir\simulations\cloudDelays.xml";                Label = "Cloud delays config" },
    @{ Path = "$FloraDir\simulations\energyConsumptionParameters.xml";Label = "Energy parameters config" },
    @{ Path = "$FloraDir\simulations\General-avg.anf";                Label = "Pre-configured analysis file (ANF)" },
    @{ Path = "$FloraDir\simulations\examples\n1000-gw1-ADR.ini";    Label = "ADR scenario (Week 1 baseline)" },
    @{ Path = "$FloraDir\simulations\examples\n1000-gw1-noADR.ini";  Label = "No-ADR control scenario" },
    @{ Path = "$FloraDir\simulations\examples\n100-gw1.ini";          Label = "100-node small scenario" },
    @{ Path = "$FloraDir\simulations\examples\n1000-gw2.ini";         Label = "2-gateway scenario" }
)

foreach ($f in $simFiles) {
    Test-FileAndReport $f.Path $f.Label
}

# ─── Results Directory ────────────────────────────────────────────────────────
Section "Simulation Results (if already run)"

$resultsDir = "$FloraDir\simulations\results"
if (Test-Path $resultsDir) {
    $scaFiles = Get-ChildItem $resultsDir -Filter "*.sca" -ErrorAction SilentlyContinue
    $vecFiles = Get-ChildItem $resultsDir -Filter "*.vec" -ErrorAction SilentlyContinue
    if ($scaFiles -and $scaFiles.Count -gt 0) {
        Write-Host "  [OK] $($scaFiles.Count) scalar result file(s) found" -ForegroundColor Green
        $pass++
        foreach ($sf in $scaFiles) {
            $szKB = [math]::Round($sf.Length / 1KB, 0)
            Write-Host "       $($sf.Name) (${szKB} KB)" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "  [INFO] No .sca files yet — run a simulation first" -ForegroundColor Gray
    }
    if ($vecFiles -and $vecFiles.Count -gt 0) {
        Write-Host "  [OK] $($vecFiles.Count) vector result file(s) found" -ForegroundColor Green
        foreach ($vf in $vecFiles) {
            $szMB = [math]::Round($vf.Length / 1MB, 1)
            Write-Host "       $($vf.Name) (${szMB} MB)" -ForegroundColor DarkGray
        }
    }
} else {
    Write-Host "  [INFO] Results directory not yet created — normal before first simulation run" -ForegroundColor Gray
}

# ─── Summary ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ("  Results: {0} passed, {1} failed" -f $pass, $fail) -ForegroundColor $(if ($fail -eq 0) {"Green"} else {"Yellow"})

if ($fail -eq 0) {
    Write-Host ""
    Write-Host "  BUILD VERIFICATION COMPLETE!" -ForegroundColor Green
    Write-Host "  FLoRa READY: Run LoRaWAN ADR for Week 1 baseline" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Next: Open OMNeT++ IDE → flora → simulations → examples" -ForegroundColor White
    Write-Host "  Run: n1000-gw1-ADR.ini → Run As → OMNeT++ Simulation" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "  SOME CHECKS FAILED." -ForegroundColor Red
    Write-Host "  See TROUBLESHOOTING.md for fixes." -ForegroundColor Yellow
}
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
