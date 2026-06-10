
# scripts/setup_env.ps1
# OMNeT++ + INET + FLoRa Environment Validator
# Run from PowerShell BEFORE starting setup to check prerequisites.
# Does NOT modify anything — read-only validation only.

param(
    [string]$OmnetRoot = "C:\omnetpp",
    [string]$SamplesDir = "C:\omnetpp\samples"
)

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  OMNeT++ / INET / FLoRa Environment Validator" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# ─── Helper Functions ────────────────────────────────────────────────────────

function Check-Pass([string]$msg) {
    Write-Host "  [PASS] $msg" -ForegroundColor Green
}

function Check-Fail([string]$msg, [string]$hint = "") {
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
    if ($hint) { Write-Host "         Hint: $hint" -ForegroundColor Yellow }
    $script:allGood = $false
}

function Check-Warn([string]$msg) {
    Write-Host "  [WARN] $msg" -ForegroundColor Yellow
}

function Check-Info([string]$msg) {
    Write-Host "  [INFO] $msg" -ForegroundColor Gray
}

function Section([string]$title) {
    Write-Host ""
    Write-Host "── $title " -ForegroundColor Cyan
}

# ─── 1. OS and Path Checks ───────────────────────────────────────────────────

Section "1. Operating System"

$os = [System.Environment]::OSVersion
Check-Info "OS: $($os.VersionString)"

if ([Environment]::Is64BitOperatingSystem) {
    Check-Pass "64-bit OS (required for OMNeT++ 6.0.3)"
} else {
    Check-Fail "32-bit OS detected" "OMNeT++ 6.0.3 requires 64-bit Windows"
}

# Check Windows version
$winVer = [System.Environment]::OSVersion.Version
if ($winVer.Major -ge 10) {
    Check-Pass "Windows 10 or later"
} else {
    Check-Warn "Windows version may be too old — Windows 10+ recommended"
}

# Check long paths
$longPathsKey = "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem"
$longPaths = Get-ItemProperty -Path $longPathsKey -Name "LongPathsEnabled" -ErrorAction SilentlyContinue
if ($longPaths -and $longPaths.LongPathsEnabled -eq 1) {
    Check-Pass "Windows long paths enabled (LongPathsEnabled=1)"
} else {
    Check-Warn "Windows long paths NOT enabled — may cause build issues"
    Check-Info "Fix: Set HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled=1 and reboot"
}

# ─── 2. Disk Space ───────────────────────────────────────────────────────────

Section "2. Disk Space"

$drive = Split-Path -Qualifier $OmnetRoot
try {
    $disk = Get-PSDrive -Name ($drive.TrimEnd(':')) -ErrorAction Stop
    $freeGB = [math]::Round($disk.Free / 1GB, 1)
    Check-Info "Free space on ${drive}: ${freeGB} GB"
    if ($freeGB -ge 10) {
        Check-Pass "Sufficient disk space (need ~6 GB: OMNeT++ 2GB + INET 2GB + FLoRa 500MB + build outputs)"
    } elseif ($freeGB -ge 5) {
        Check-Warn "Tight on disk space (${freeGB} GB free, 6+ GB recommended)"
    } else {
        Check-Fail "Insufficient disk space (${freeGB} GB free)" "Need at least 6 GB for full build"
    }
} catch {
    Check-Warn "Could not check disk space for $drive"
}

# ─── 3. OMNeT++ Installation ─────────────────────────────────────────────────

Section "3. OMNeT++ Installation"

if (Test-Path $OmnetRoot) {
    Check-Pass "OMNeT++ root exists: $OmnetRoot"
} else {
    Check-Fail "OMNeT++ root not found: $OmnetRoot" "Extract omnetpp-6.0.3-windows-x86_64.zip to C:\omnetpp"
}

# Check for key OMNeT++ files
$keyFiles = @(
    @{ Path = "$OmnetRoot\mingwenv.cmd";             Desc = "MinGW shell launcher" },
    @{ Path = "$OmnetRoot\configure";                Desc = "Build configure script" },
    @{ Path = "$OmnetRoot\Makefile";                 Desc = "Root Makefile" },
    @{ Path = "$OmnetRoot\ide\omnetpp.exe";          Desc = "OMNeT++ IDE" },
    @{ Path = "$OmnetRoot\mingw64\bin\gcc.exe";      Desc = "MinGW GCC compiler" }
)

foreach ($f in $keyFiles) {
    if (Test-Path $f.Path) {
        Check-Pass "$($f.Desc) found"
    } else {
        Check-Fail "$($f.Desc) NOT found: $($f.Path)" "Re-extract OMNeT++ zip or check extraction path"
    }
}

# Check if OMNeT++ is built (opp_run exists)
$oppRun = "$OmnetRoot\bin\opp_run.exe"
if (Test-Path $oppRun) {
    Check-Pass "OMNeT++ is built (opp_run.exe exists)"
} else {
    Check-Warn "OMNeT++ not yet built — run 'make' inside mingwenv.cmd"
    Check-Info "Steps: open $OmnetRoot\mingwenv.cmd → ./configure → make -j4"
}

# ─── 4. INET Installation ────────────────────────────────────────────────────

Section "4. INET Framework"

# Look for INET in expected locations
$inetCandidates = @(
    "$SamplesDir\inet4.4",
    "$SamplesDir\inet",
    "$SamplesDir\inet-4.4.1",
    "$SamplesDir\inet-4.4.2"
)

$inetFound = $null
foreach ($candidate in $inetCandidates) {
    if (Test-Path $candidate) {
        $inetFound = $candidate
        break
    }
}

if ($inetFound) {
    Check-Pass "INET directory found: $inetFound"

    # Check .project exists
    if (Test-Path "$inetFound\.project") {
        Check-Pass "INET .project file exists (importable into IDE)"
    } else {
        Check-Fail "INET .project file missing" "Re-extract INET zip or use git clone"
    }

    # Check INET version
    $changelogCandidates = @("$inetFound\CHANGELOG.md", "$inetFound\CHANGES", "$inetFound\CHANGES.md")
    foreach ($cl in $changelogCandidates) {
        if (Test-Path $cl) {
            $firstLine = Get-Content $cl -First 3 | Out-String
            Check-Info "INET Changelog: $($firstLine.Trim())"
            break
        }
    }

    # Check if built
    $inetDllCandidates = @(
        "$inetFound\out\gcc-release\src\INET.dll",
        "$inetFound\out\gcc-debug\src\INET_dbg.dll",
        "$inetFound\out\clang-release\src\INET.dll"
    )
    $inetBuilt = $false
    foreach ($dll in $inetDllCandidates) {
        if (Test-Path $dll) {
            $inetBuilt = $true
            Check-Pass "INET is built: $(Split-Path $dll -Leaf) found"
            break
        }
    }
    if (-not $inetBuilt) {
        Check-Warn "INET not yet built — import into IDE and Build Project"
    }
} else {
    Check-Fail "INET not found in $SamplesDir" "Download INET 4.4.1 from https://github.com/inet-framework/inet/archive/refs/tags/v4.4.1.zip and extract to $SamplesDir\inet4.4"
}

# ─── 5. FLoRa Installation ───────────────────────────────────────────────────

Section "5. FLoRa Simulator"

$floraCandidates = @(
    "$SamplesDir\flora",
    "$SamplesDir\flora-1.1.0"
)

$floraFound = $null
foreach ($candidate in $floraCandidates) {
    if (Test-Path $candidate) {
        $floraFound = $candidate
        break
    }
}

if ($floraFound) {
    Check-Pass "FLoRa directory found: $floraFound"

    # Check key files
    $floraFiles = @(
        @{ Path = "$floraFound\.project";                    Desc = ".project (IDE import)" },
        @{ Path = "$floraFound\src";                         Desc = "src/ directory" },
        @{ Path = "$floraFound\simulations\omnetpp.ini";     Desc = "Default simulation ini" },
        @{ Path = "$floraFound\simulations\examples\n1000-gw1-ADR.ini"; Desc = "ADR scenario ini" }
    )
    foreach ($f in $floraFiles) {
        if (Test-Path $f.Path) {
            Check-Pass "$($f.Desc) found"
        } else {
            Check-Fail "$($f.Desc) NOT found: $($f.Path)" "Re-clone FLoRa: git clone https://github.com/florasim/flora.git"
        }
    }

    # Check FLoRa version
    $versionFile = "$floraFound\Version"
    if (Test-Path $versionFile) {
        $ver = Get-Content $versionFile -First 1
        Check-Info "FLoRa version: $ver"
        if ($ver -match "1\.1\.0") {
            Check-Pass "FLoRa v1.1.0 confirmed (correct version for INET 4.4.x)"
        } else {
            Check-Warn "FLoRa version is '$ver' — expected 1.1.0 for INET 4.4.x compatibility"
        }
    }

    # Check if built
    $floraExe = "$floraFound\src\flora.exe"
    if (Test-Path $floraExe) {
        Check-Pass "FLoRa is built (flora.exe found)"
    } else {
        Check-Warn "FLoRa not yet built — import into IDE, set Project References to inet4.4, then Build"
    }

} else {
    Check-Fail "FLoRa not found in $SamplesDir" "Clone: git clone https://github.com/florasim/flora.git $SamplesDir\flora"
}

# ─── 6. Network (optional, for downloads) ────────────────────────────────────

Section "6. Network Connectivity (for downloads)"

try {
    $ping = Test-NetConnection -ComputerName "github.com" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($ping) {
        Check-Pass "GitHub.com reachable (HTTPS)"
    } else {
        Check-Warn "Cannot reach github.com — downloads may fail"
    }
} catch {
    Check-Warn "Could not test network connectivity"
}

# ─── 7. Git (optional) ───────────────────────────────────────────────────────

Section "7. Git (optional)"

$gitPath = Get-Command git -ErrorAction SilentlyContinue
if ($gitPath) {
    $gitVer = git --version 2>&1
    Check-Pass "Git found: $gitVer"
} else {
    Check-Warn "Git not found in system PATH — use ZIP downloads as alternative"
    Check-Info "Git is available INSIDE the OMNeT++ MinGW shell (mingwenv.cmd)"
}

# ─── Summary ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "  ALL CHECKS PASSED — Ready to proceed!" -ForegroundColor Green
} else {
    Write-Host "  SOME CHECKS FAILED — See FAIL items above." -ForegroundColor Red
    Write-Host "  Refer to SETUP_GUIDE.md for resolution steps." -ForegroundColor Yellow
}
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Fix any FAIL items above"
Write-Host "  2. Open $OmnetRoot\mingwenv.cmd"
Write-Host "  3. Follow SETUP_GUIDE.md Phase 2 through Phase 5"
Write-Host "  4. First simulation: flora/simulations/omnetpp.ini"
Write-Host "  5. ADR baseline: flora/simulations/examples/n1000-gw1-ADR.ini"
Write-Host ""
