# Troubleshooting Guide: FLoRa + INET + OMNeT++ on Windows

---

## Error Index

| Error | Quick Fix |
|-------|-----------|
| Duplicate symbol linker error | Use INET 4.4.1 (not 4.4.0) |
| fatal error: inet/physicallayer/... No such file | Set Project References |
| INET_dbg linker error | Add -lINET in Makemake Link tab |
| .project missing | Import Existing Projects manually |
| Build succeeded but run crashes | Check INET version compatibility |
| Qtenv won't start | Install OpenSSL / VC++ Redistributables |
| "No such module INET" at runtime | INET not on NED path |
| Git clone fails | Use zip download instead |
| Build is extremely slow | Normal on Windows — use make -j$(nproc) |

---

## Problem 1: Duplicate Symbol Linker Errors (Most Common on Windows)

### Symptom
```
lld-link: error: duplicate symbol: inet::SharingTagSet::setTag(...)
lld-link: error: duplicate symbol: virtual thunk to inet::physicallayer::Radio::getMedium()
lld-link: error: 1890 duplicate symbols
```

### Cause
INET 4.4.0 is missing `INET_API` export annotations on template classes.
This was a known Windows-specific bug in INET 4.4.0.

### Fix
Switch from INET 4.4.0 to **INET 4.4.1**:
1. Download INET 4.4.1: `https://github.com/inet-framework/inet/archive/refs/tags/v4.4.1.zip`
2. Extract and replace your existing `C:\omnetpp\samples\inet4.4\` folder
3. Re-import into IDE: File → Import → Existing Projects
4. Clean INET: Project → Clean → select inet4.4 → OK
5. Rebuild INET and then FLoRa

---

## Problem 2: INET Headers Not Found

### Symptom
```
fatal error: inet/physicallayer/wireless/common/analogmodel/packetlevel/ScalarReception.h:
  No such file or directory
Building file: src/LoRaPhy/LoRaRadio.cc
```

### Cause
FLoRa project does not have INET set as a project reference.

### Fix — Set Project References
1. In Project Explorer, right-click `flora` → **Properties**
2. Left panel: click **Project References**
3. **Check the checkbox** next to `inet` (or `inet4.4`)
4. Click **Apply and Close**
5. Clean and rebuild flora

### Fix — Verify NED Source Folders (if above didn't help)
1. Right-click `flora` → **Properties → OMNeT++ → NED Source Folders**
2. Ensure `src` is listed as a NED source folder
3. Right-click `inet4.4` → same check

---

## Problem 3: INET_dbg Linker Error / "cannot find -lINET_dbg"

### Symptom
```
/usr/bin/ld: cannot find -lINET_dbg
collect2: error: ld returned 1 exit status
```

### Cause
The flora project is trying to link a debug build of INET that doesn't exist.

### Fix — Option A: Build INET in Debug Mode (matches flora's mode)
1. In Project Explorer, select `inet4.4`
2. Click the dropdown arrow next to the Build button → **Build Configurations → Set Active → debug**
3. Build INET in debug mode
4. Then rebuild flora

### Fix — Option B: Switch Flora to Release Mode
1. Right-click `flora` → **Properties → OMNeT++ → Makemake**
2. Select `src` entry → **Options → Link tab**
3. In **Additional libraries**, replace `-lINET_dbg` with `-lINET`
4. Alternatively, set Active Build Configuration to `release` for flora:
   Right-click `flora` → **Build Configurations → Set Active → release**

### Fix — Option C: Match build modes
- If INET is built as `release`, set flora to `release`
- If INET is built as `debug`, set flora to `debug`
- Right-click project → **Build Configurations → Set Active**

---

## Problem 4: `.project` File Missing (Can't Import)

### Symptom
When using File → Import, the flora (or inet) folder does not appear as a detectable project.

### Fix — Create Missing .project for FLoRa
If the `.project` file is missing from the flora folder:
1. **File → New → OMNeT++ Project**
2. Enter project name: `flora`
3. For "Project location": uncheck "Use default location" → Browse to `C:\omnetpp\samples\flora`
4. Next → Next → Finish
5. Then add source folders and references manually
6. Or clone fresh: `git clone https://github.com/florasim/flora.git`  
   The official repo includes `.project` and `.cproject` — missing files indicate a corrupted download

### Verify .project exists
In MinGW shell:
```bash
ls -la /c/omnetpp/samples/flora/.project
ls -la /c/omnetpp/samples/flora/.cproject
```
Both files must exist. If not, re-clone or re-extract the source.

---

## Problem 5: "No Such Module" or NED Lookup Failure at Runtime

### Symptom
```
Error during startup: Module type not found: flora.simulations.LoRaNetworkTest
```
or
```
Component type not found: inet.physicallayer.wireless.common.medium.RadioMedium
```

### Fix
The INET NED package is not on the path.
In Run Configuration:
1. Run → Run Configurations
2. Select your flora simulation
3. Go to the **Simulation** tab
4. In **NED path**, ensure both paths are present (separated by `;` on Windows):
   ```
   C:\omnetpp\samples\flora\src;C:\omnetpp\samples\inet4.4\src
   ```
5. Or simpler: right-click `flora` → **Properties → Project References** → ensure inet4.4 is checked

---

## Problem 6: Simulation Crashes at Start / "Segmentation Fault"

### Symptom
Qtenv opens but immediately crashes, or Cmdenv shows segfault.

### Possible Causes and Fixes

**A. Wrong INET version**
- Verify INET version: in MinGW shell:
  ```bash
  grep -r "version" /c/omnetpp/samples/inet4.4/CHANGES | head -5
  ```
- Must be 4.4.1 or 4.4.2 for FLoRa v1.1.0

**B. Mixed debug/release libraries**
- FLoRa.exe (debug) trying to load INET.dll (release) = crash
- Solution: rebuild both in same mode (both release OR both debug)

**C. Out-of-date .vec/.sca result files**
- Delete `simulations/results/` folder and re-run

---

## Problem 7: Build Works But "flora.exe" Not Found

### Symptom
Build console shows no errors, but the run button gives an error about missing executable.

### Fix
```bash
# Check where the build output actually went
find /c/omnetpp/samples/flora -name "flora.exe" 2>/dev/null
find /c/omnetpp/samples/flora -name "*.exe" 2>/dev/null
```

If in `out/gcc-release/src/flora.exe` instead of `src/flora.exe`:
- The IDE run configuration might be looking in the wrong place
- Run directly: `out/gcc-release/src/flora.exe -u Qtenv simulations/omnetpp.ini`

---

## Problem 8: Very Slow Build on Windows

### Symptom
Build takes 45+ minutes — completely normal on Windows due to NTFS overhead.

### Mitigation
```bash
# Build with all CPU cores
make -j$(nproc)

# Or specify manually
make -j8

# Add to .bashrc inside MinGW for permanent effect
export MAKEFLAGS="-j$(nproc)"
```

Additional speedup: Enable Windows long paths (reduces filesystem calls):
1. `Win+R` → `regedit`
2. Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`
3. Set `LongPathsEnabled` to `1`
4. Reboot

---

## Problem 9: Git Clone Fails or Times Out

### Symptom
```
fatal: unable to access 'https://github.com/florasim/flora.git/': Could not resolve host
```
or clone hangs.

### Fix — Use ZIP Download Instead
1. Go to `https://github.com/florasim/flora/archive/refs/tags/v1.1.0.zip`
2. Download and extract to `C:\omnetpp\samples\flora\`

### Fix — Use Git Inside MinGW Shell
Regular Windows git may not be configured in the OMNeT++ shell:
```bash
# Inside mingwenv.cmd shell
git --version    # should show git version

# Clone with verbose output
GIT_CURL_VERBOSE=1 git clone https://github.com/florasim/flora.git
```

---

## Problem 10: OMNeT++ IDE Won't Launch / Java Error

### Symptom
```
A Java Runtime Environment (JRE) or Java Development Kit (JDK) must be available...
```

### Fix
OMNeT++ 6.0 bundles its own JRE. Check:
```
C:\omnetpp\tools\win64\jre\
```
If missing, re-extract the full OMNeT++ zip (the file may have been partially extracted).

---

## Version Compatibility Reference

```
┌─────────────────┬──────────────┬──────────────────────────────────────┐
│ OMNeT++ Version │ INET Version │ FLoRa Compatibility                  │
├─────────────────┼──────────────┼──────────────────────────────────────┤
│ 5.x             │ 3.x          │ FLoRa v0.7.1 / v0.8 only            │
│ 6.0.x           │ 4.3.1        │ FLoRa 1.0.0 (limited, issues on Win) │
│ 6.0.x           │ 4.4.0        │ FLoRa 1.1.0 (Windows linker bug)    │
│ 6.0.x           │ 4.4.1 ✓     │ FLoRa 1.1.0 — RECOMMENDED           │
│ 6.0.x           │ 4.4.2 ✓     │ FLoRa 1.1.0 — also works            │
│ 6.0.x           │ 4.5.x ✗     │ Incompatible (API breaking changes)  │
│ 6.0.x           │ 4.6.x ✗     │ Incompatible (requires OMNeT++ 6.2+) │
│ 6.1.x           │ 4.4.2 ✓     │ FLoRa 1.1.0 (not officially tested) │
│ 6.2.x / 6.3.x  │ 4.4.x        │ Untested with FLoRa                 │
└─────────────────┴──────────────┴──────────────────────────────────────┘
```

---

## Quick Diagnostic Checklist

Run these checks when something goes wrong:

```bash
# In MinGW shell:

# 1. Is OMNeT++ built?
opp_run --version

# 2. Is INET built?
ls /c/omnetpp/samples/inet4.4/out/gcc-*/src/INET*

# 3. Is FLoRa built?
ls /c/omnetpp/samples/flora/src/flora.exe

# 4. What INET version?
head -5 /c/omnetpp/samples/inet4.4/CHANGELOG.md

# 5. What FLoRa version?
cat /c/omnetpp/samples/flora/Version

# 6. Does .project exist?
ls -la /c/omnetpp/samples/flora/.project
ls -la /c/omnetpp/samples/inet4.4/.project

# 7. Check build errors in log
make -C /c/omnetpp/samples/flora 2>&1 | grep -i error | head -20
```
