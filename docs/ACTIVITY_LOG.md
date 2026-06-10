# OMNeT++ + INET + FLoRa — Full Setup Activity Log
**Date:** March 8, 2026  
**OS:** Windows 10/11 (Build 26200), 64-bit  
**Disk free:** 293.5 GB  

---

## Phase 1 — Research & Compatibility Verification

**Goal:** Confirm the exact compatible versions before downloading anything.

| Component | Version Selected | Reason |
|-----------|-----------------|--------|
| OMNeT++ | 6.0.3 | Latest stable Windows release |
| INET | 4.4.1 | Best for Windows — fixes duplicate symbol linker errors present in 4.4.0 |
| FLoRa | v1.1.0 | Only tagged release; targets INET 4.4.x |

**Key findings:**
- INET 4.4.3 does not exist (series ends at 4.4.2)
- FLoRa has no `inet4` branch — only `master` with tag `v1.1.0`
- INET 4.4.1 preferred over 4.4.2 on Windows to avoid known linker issues

---

## Phase 2 — Documentation Created

Nine reference files written to `c:\omnet-workspace\`:

| File | Purpose |
|------|---------|
| `README.md` | Master overview, 30-minute phase plan |
| `SETUP_GUIDE.md` | Full step-by-step install guide (phases 1–6) |
| `SIMULATION_GUIDE.md` | Simulation configs, ADR params, CSV export commands |
| `TROUBLESHOOTING.md` | 10 known error scenarios with exact fixes |
| `VERSION_NOTES.md` | Verified compatibility matrix and Windows caveats |
| `SETUP_PROGRESS.md` | Live build status tracker |
| `scripts/setup_env.ps1` | Pre-install validator (read-only checks) |
| `scripts/verify_build.ps1` | Post-build verification script |
| `scripts/build_all.sh` | MinGW shell auto-build for INET + FLoRa |
| `scripts/quick_start.bat` | Double-click shortcut to open MinGW shell |

---

## Phase 3 — System Validation

Ran pre-install checks:

```
git     → C:\Program Files\Git\cmd\git.exe   ✅
curl    → C:\WINDOWS\system32\curl.exe        ✅
7za     → C:\omnetpp\tools\7za.exe            ✅ (bundled)
OMNeT++ → not yet installed                   ⏳
```

Created directory structure:
```
C:\omnetpp\                  ← OMNeT++ install target
C:\omnetpp\samples\
c:\omnet-workspace\downloads\  ← archives
c:\omnet-workspace\results\    ← simulation outputs
```

---

## Phase 4 — OMNeT++ 6.0.3 Installation

### 4a. Download
- Method: Windows BITS transfer (Background Intelligent Transfer Service)
- File: `omnetpp-6.0.3-windows-x86_64.zip`
- Size: **846.2 MB**
- Saved to: `c:\omnet-workspace\downloads\`

### 4b. Extraction
- Extracted ZIP to `C:\` using `ZipFile::ExtractToDirectory`
- Renamed extracted folder to `C:\omnetpp`
- Confirmed: `mingwenv.cmd` present, `Version = omnetpp-6.0.3`

### 4c. MinGW Toolchain Extraction
The OMNeT++ Windows zip contains 7z archives that must be extracted separately:

```powershell
# GCC 12.1.0 toolchain (429 MB)
7za.exe x -aos -y -otools\win32.x86_64 opp-tools-win32-x86_64-mingw64-toolchain.7z

# Qt5 + OpenSceneGraph dependencies (54 MB)
7za.exe x -aos -y -otools\win32.x86_64 opp-tools-win32-x86_64-mingw64-dependencies.7z
```

Result:
```
C:\omnetpp\tools\win32.x86_64\mingw64\bin\gcc.exe   → GCC 12.1.0
C:\omnetpp\tools\win32.x86_64\opt\mingw64\bin\qmake → Qt5
```

### 4d. Qt Binary Patcher
```
qtbinpatcher.exe → "Patching not needed" (paths already correct)
```

### 4e. Configure
Required environment variables before running bash:
```powershell
$env:HOME    = "C:\omnetpp\"
$env:MSYSTEM = "MINGW64"
```

`./configure` output — all dependencies detected:
```
GCC 12.1.0           ✅
Qt5 (qmake)          ✅  /opt/mingw64/bin/qmake
OpenSceneGraph 3.5.5 ✅
Perl                 ✅
SWIG                 ✅
Python3              ✅
→ Makefile.inc generated
```

### 4f. Build OMNeT++ Runtime
```bash
make -j4   # 4 parallel jobs
```
Built in order: `liboppcommon.dll` → `libopplayout.dll` → `liboppeventlog.dll` → `liboppnedxml.dll` → `liboppscave.dll` → `liboppsim.dll` → `liboppcmdenv.dll` → `liboppenvir.dll` → `liboppqtenv.dll` → `opp_run.exe`

**Verified:**
```
C:\omnetpp\bin\opp_run.exe     → Version: 6.0.3  ✅
C:\omnetpp\bin\                → 29 files total
```

---

## Phase 5 — INET 4.4.1 Build

### 5a. Download
- Method: `curl.exe -L` (BITS failed due to GitHub redirects)
- File: `inet-4.4.1-src.tgz` / zip
- Size: **24.5 MB**
- Extracted to: `c:\omnet-workspace\inet4.4\`

### 5b. Build
```bash
source /c/omnet-workspace/inet4.4/setenv   # sets up inet_root
cd /c/omnet-workspace/inet4.4
make makefiles                             # generates src/Makefile
make -j4 MODE=release                     # ~15–25 min
```

Progress tracked: 619 → 731 → 911 → 1128 → 1461 → 1518 object files compiled

**Verified:**
```
inet4.4\out\clang-release\src\libINET.dll  → 41.3 MB  ✅
```

---

## Phase 6 — FLoRa v1.1.0 Build

### 6a. Clone
```bash
git clone https://github.com/florasim/flora.git
git checkout v1.1.0
```
- Location: `c:\omnet-workspace\flora\`
- Confirmed: tag `v1.1.0`, `Version` file = `flora-1.1.0`

### 6b. Makefile (FLoRa's Makefile already has `INET_DIR = ../inet4.4`)
```bash
source /c/omnet-workspace/inet4.4/setenv
cd /c/omnet-workspace/flora
make makefiles   # → Creating Makefile in /c/omnet-workspace/flora/src
```

### 6c. Build
```bash
make -j4 MODE=release
```

Output: compiled 6 `.msg` files + 16 `.cc` files, then:
```
Creating shared library: ../out/clang-release/src/libflora.dll
BUILD_STATUS=True
```

Minor warnings only (missing `override` keyword in `LoRaMedium.h`) — no errors.

**Verified:**
```
flora\out\clang-release\src\libflora.dll  → 3.8 MB  ✅
```

---

## Phase 7 — First Simulation Run

```bash
source /c/omnet-workspace/inet4.4/setenv
cd /c/omnet-workspace/flora/simulations
INET_ROOT=/c/omnet-workspace/inet4.4
PATH=$INET_ROOT/src:$PATH

opp_run \
  -l ../out/clang-release/src/flora \
  -n .:../src:$INET_ROOT/src \
  -u Cmdenv --sim-time-limit=5min -r 0 omnetpp.ini
```

**Output:**
```
Loading NED files from ..src: 22
Loading NED files from inet4.4/src: 1166
Setting up network "flora.simulations.LoRaNetworkTest"...
Running simulation...
** Event #0   t=0   Elapsed: 5e-06s   0% completed
** Event #3   t=300  Elapsed: 0.001396s  100% completed
<!> Simulation time limit reached -- at t=300s, event #3
Calling finish()...
```

**Result: Simulation completed successfully ✅**

---

## Phase 8 — run_project.ps1 Script

Created `c:\omnet-workspace\run_project.ps1` — a single script to launch any FLoRa simulation configuration.

### Usage

```powershell
cd C:\omnet-workspace

.\run_project.ps1                           # Quick test (1 node, 5 min simtime)
.\run_project.ps1 -Config n100-gw1          # 100 nodes, 1 gateway
.\run_project.ps1 -Config n1000-gw1-ADR     # 1000 nodes, ADR enabled (1-day sim)
.\run_project.ps1 -Config n1000-gw1-noADR   # 1000 nodes, no ADR
.\run_project.ps1 -Config n1000-gw2         # 1000 nodes, 2 gateways
.\run_project.ps1 -Gui                      # Open Qtenv visual window
.\run_project.ps1 -Config n100-gw1 -Run 2   # Choose repeat index
```

### What the script does
1. Pre-flight checks: verifies `opp_run.exe`, `libINET.dll`, `libflora.dll` exist
2. Sources INET environment (`setenv`)
3. Resolves the correct `.ini` file for the chosen config
4. Launches `opp_run` with `-l flora -n .:src:inet/src` in Cmdenv or Qtenv
5. Prints results path and `opp_scavetool` CSV export hint on success

### Bug fixed
PowerShell `Set-StrictMode -Version Latest` was expanding `\$INET_ROOT` as a PS variable inside the bash here-string, causing `exit code 1`. Fixed by using `` `$INET_ROOT `` (PowerShell backtick escape) for all bash variables.

---

## Final Verified State

| Component | Status | Location |
|-----------|--------|----------|
| OMNeT++ 6.0.3 | ✅ Built | `C:\omnetpp\bin\opp_run.exe` |
| GCC 12.1.0 | ✅ Ready | `C:\omnetpp\tools\win32.x86_64\mingw64\bin\gcc.exe` |
| Qt5 | ✅ Ready | `C:\omnetpp\tools\win32.x86_64\opt\mingw64\bin\qmake.exe` |
| INET 4.4.1 | ✅ Built | `inet4.4\out\clang-release\src\libINET.dll` (41.3 MB) |
| FLoRa v1.1.0 | ✅ Built | `flora\out\clang-release\src\libflora.dll` (3.8 MB) |
| First simulation | ✅ Ran | `General` config, t=300s, Event #3, no errors |

---

## Available Simulation Configs

| Config | Nodes | Gateways | ADR | Sim Time | Repeats |
|--------|-------|----------|-----|----------|---------|
| `quick` (omnetpp.ini General) | 1 | 1 | Yes | 5 min (test) | 1 |
| `n100-gw1` | 100 | 1 | Yes | 1 day | 5 |
| `n1000-gw1-ADR` | 1000 | 1 | Yes | 1 day | 5 |
| `n1000-gw1-noADR` | 1000 | 1 | No | 1 day | 5 |
| `n1000-gw2` | 1000 | 2 | Yes | 1 day | 5 |

---

## How to Open the Visual Simulation (Qtenv)

```powershell
cd C:\omnet-workspace
.\run_project.ps1 -Gui
```

In the Qtenv window:
- **▶ Run** (`F5`) — start simulation with animation
- **⏩ Fast** (`F6`) — run at max speed, no animation
- **⏸ Pause** — inspect current state
- **Double-click any module** — inspect LoRa parameters (SF, BW, TP, CR)
- **Log panel** (bottom) — live event stream

## How to Export Results to CSV

```bash
cd C:\omnet-workspace\flora\simulations
opp_scavetool export results/General-0.sca -o ../../results/output.csv
```

---

## Key Lessons / Troubleshooting Notes

| Problem | Fix |
|---------|-----|
| BITS transfer fails for GitHub URLs | Use `curl.exe -L` instead |
| `gcc not found` in bash | Set `$env:MSYSTEM="MINGW64"` before invoking bash |
| MinGW toolchain missing after ZIP extract | Must separately extract `.7z` archives with bundled `7za.exe` |
| INET `make` fails without `inet_root` | Run `source setenv` first |
| FLoRa's `run_flora` points to `inet4.3` | Bypass it; call `opp_run` directly with `-l` and `-n` flags |
| PS variables expanding inside bash here-string | Use backtick escape `` `$VAR `` not `\$VAR` in PowerShell `@"..."@` blocks |
