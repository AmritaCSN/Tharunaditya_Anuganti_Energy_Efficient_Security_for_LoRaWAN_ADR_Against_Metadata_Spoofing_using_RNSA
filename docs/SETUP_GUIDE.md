# Complete Setup Guide: OMNeT++ 6.0.3 + INET 4.4.1 + FLoRa 1.1.0 on Windows

---

## Phase 1 — Downloads

### 1.1 OMNeT++ 6.0.3 Windows Bundle

**URL:**
```
https://github.com/omnetpp/omnetpp/releases/download/omnetpp-6.0.3/omnetpp-6.0.3-windows-x86_64.zip
```

- Size: ~846 MB
- Contains: MinGW64 toolchain, Eclipse IDE, all required libraries
- Bundled toolchain: MinGW-w64 GCC — No separate compiler installation needed

> Note: OMNeT++ 6.3.0 is the latest as of March 2026, but FLoRa 1.1.0 formal
> support is for 6.0.x. Use 6.0.3 for a guaranteed working setup.

### 1.2 INET Framework 4.4.1

**URL:**
```
https://github.com/inet-framework/inet/releases/tag/v4.4.1
```
**Direct zip:**
```
https://github.com/inet-framework/inet/archive/refs/tags/v4.4.1.zip
```

- Why 4.4.1 and not 4.4.0: INET 4.4.1 (July 2022) fixes critical duplicate-symbol
  linker errors on Windows that affect all projects depending on INET, including FLoRa.
- Why not 4.4.2: Also works. 4.4.2 adds OMNeT++ 6.1 compatibility fixes.
  Either 4.4.1 or 4.4.2 will work — 4.4.1 is safer.
- Why not 4.5.x / 4.6.x: INET 4.5+ introduced breaking API changes.
  FLoRa has not been migrated. INET 4.6 requires OMNeT++ 6.2+.

### 1.3 FLoRa v1.1.0

**GitHub repository:**
```
https://github.com/florasim/flora
```
**Release page:**
```
https://github.com/florasim/flora/releases/tag/v1.1.0
```
**Direct zip:**
```
https://github.com/florasim/flora/archive/refs/tags/v1.1.0.zip
```

> Note: There is only ONE branch in florasim/flora: `master`.
> There is no "inet4" branch. v1.1.0 is the latest tag (June 9, 2022).
> This release explicitly targets INET 4.4.0 (compatible with 4.4.1 and 4.4.2).

---

## Phase 2 — Install OMNeT++

### 2.1 Extract Archive

1. Extract `omnetpp-6.0.3-windows-x86_64.zip`
2. **IMPORTANT**: Place at `C:\omnetpp` (root, short path — avoids Windows 260-char path limit)
   ```
   C:\omnetpp\          ← the OMNeT++ root
   C:\omnetpp\bin\
   C:\omnetpp\samples\  ← we will put inet4.4 and flora here
   C:\omnetpp\ide\      ← Eclipse IDE
   C:\omnetpp\mingw64\  ← bundled GCC toolchain
   ```

> ⚠ Do NOT extract to C:\Users\YourName\Downloads\ or any deep path.
> Deep paths cause build failures due to Windows MAX_PATH limits.

### 2.2 Open the OMNeT++ Shell

Navigate to `C:\omnetpp` and double-click `mingwenv.cmd`.
This opens a MinGW/MSYS bash shell with the full OMNeT++ build environment.

**All build operations must be done inside this shell.**

### 2.3 Build OMNeT++ (first-time only)

Inside the MinGW shell:
```bash
cd /c/omnetpp

# Configure (optionally disable graphical features you don't need)
./configure

# Build with all available CPU cores (takes 5-15 minutes)
make -j$(nproc)
```

**Expected output at the end:**
```
make[1]: Leaving directory '/c/omnetpp'
```

**Verify OMNeT++ is built:**
```bash
which opp_run
opp_run --version
# Output: OMNeT++ Discrete Event Simulation  (C) 1992-2022 Andras Varga, OpenSim Ltd.
#         Version: 6.0.3, build: 221009-...
```

### 2.4 Launch the OMNeT++ IDE

```bash
omnetpp
```
Or double-click `C:\omnetpp\ide\omnetpp.exe`.

When asked to select a workspace, enter:
```
C:\omnetpp\samples
```
This keeps all projects in one place with short paths — critical on Windows.

---

## Phase 3 — Import and Build INET

### 3.1 Prepare INET Source

Extract `inet-4.4.1.zip` and rename/move the extracted folder:
```
C:\omnetpp\samples\inet4.4\
```
(The zip extracts to `inet-4.4.1\` — rename it to `inet4.4` for convenience.)

The structure should be:
```
C:\omnetpp\samples\inet4.4\
├── src\
├── examples\
├── tests\
├── Makefile
├── .project    ← Eclipse project file — must exist
└── README.md
```

### 3.2 Import INET into OMNeT++ IDE

1. Open OMNeT++ IDE
2. Go to **File → Import...**
3. Select **General → Existing Projects into Workspace** → Next
4. Set **Root directory** to `C:\omnetpp\samples\inet4.4`
5. The project `inet` should appear in the list with a checkbox checked
6. Click **Finish**

### 3.3 Build INET

1. In the Project Explorer, right-click on `inet` → **Build Project**
   (or press `Ctrl+B` with `inet` selected)
2. Wait for the build to complete — this takes **5-15 minutes** on first build
3. Expected console output:
   ```
   make[1]: Entering directory '/c/omnetpp/samples/inet4.4'
   ...
   make[1]: Leaving directory '/c/omnetpp/samples/inet4.4'
   Build finished (0 errors, 0 warnings)
   ```

> ⚠ If you see linker errors with INET 4.4.0, switch to INET 4.4.1 (fixes Windows-specific
> duplicate symbol errors in template classes).

### 3.4 Verify INET Build Output

After successful build, verify the library exists:
```
C:\omnetpp\samples\inet4.4\out\gcc-release\src\INET.dll
```
Or in MinGW shell:
```bash
ls /c/omnetpp/samples/inet4.4/out/gcc-*/src/INET*
```

---

## Phase 4 — Import and Build FLoRa

### 4.1 Prepare FLoRa Source

**Option A: Download zip**
Extract `flora-1.1.0.zip` and move to:
```
C:\omnetpp\samples\flora\
```

**Option B: Git clone (recommended — easier to update)**
Inside the MinGW shell:
```bash
cd /c/omnetpp/samples
git clone https://github.com/florasim/flora.git flora
cd flora
git checkout v1.1.0
```

The folder structure should be:
```
C:\omnetpp\samples\flora\
├── src\
│   ├── LoRa\
│   ├── LoRaApp\
│   ├── LoRaEnergyModules\
│   └── LoRaPhy\
├── simulations\
│   ├── omnetpp.ini
│   ├── package.ned
│   ├── cloudDelays.xml
│   ├── energyConsumptionParameters.xml
│   ├── General-avg.anf
│   └── examples\
│       ├── n100-gw1.ini
│       ├── n1000-gw1-ADR.ini
│       ├── n1000-gw1-noADR.ini
│       └── n1000-gw2.ini
├── .project
├── .cproject
├── Makefile
└── README.md
```

### 4.2 Import FLoRa into OMNeT++ IDE

1. **File → Import... → General → Existing Projects into Workspace**
2. Set **Root directory** to `C:\omnetpp\samples\flora`
3. Project `flora` should appear → click **Finish**

### 4.3 Set Project References (CRITICAL STEP)

FLoRa must be linked to INET. This step is frequently missed and causes most build errors.

1. In Project Explorer, right-click on `flora` → **Properties**
2. Navigate to **Project References** in the left panel
3. **Check the box** next to `inet4.4` (or `inet` — whatever INET is named in your IDE)
4. Click **Apply and Close**

### 4.4 Configure Build Settings (Makemake)

1. Right-click `flora` → **Properties → OMNeT++ → Makemake**
2. Select the `src` folder entry → click **Options...**
3. Go to the **Link** tab
4. Under **Additional objects, libraries, library folders**:
   - Ensure `-lINET` (or equivalent) is listed
   - If missing: add `-lINET` in the libraries field
5. Click **OK → Apply and Close**

> In most cases with Project References set correctly, this step is automatic.
> Only do manually if you see "INET_dbg" or undefined symbol linker errors.

### 4.5 Build FLoRa

1. Right-click `flora` → **Build Project** (or `Ctrl+B`)
2. Expected console output:
   ```
   make[1]: Entering directory '/c/omnetpp/samples/flora'
   ...
   Building file src/LoRa/LoRaGWMac.cc
   Building file src/LoRaPhy/LoRaRadio.cc
   ...
   make[1]: Leaving directory '/c/omnetpp/samples/flora'
   Build finished (0 errors, 0 warnings)
   ```
3. Verify the executable exists:
   ```bash
   ls /c/omnetpp/samples/flora/src/flora.exe
   ```

---

## Phase 5 — Run Your First Simulation

### 5.1 Simulation Configurations Available

| File | Nodes | Gateways | ADR | Description |
|------|-------|----------|-----|-------------|
| `simulations/omnetpp.ini` | 1 | 1 | Off | Default, simplest — start here |
| `simulations/examples/n100-gw1.ini` | 100 | 1 | Off | Small network |
| `simulations/examples/n1000-gw1-ADR.ini` | 1000 | 1 | **On** | ADR enabled — Week 1 baseline |
| `simulations/examples/n1000-gw1-noADR.ini` | 1000 | 1 | Off | Comparison without ADR |
| `simulations/examples/n1000-gw2.ini` | 1000 | 2 | Off | Multi-gateway scenario |

### 5.2 Run the Default Simulation (Start Here)

1. In Project Explorer, expand `flora` → `simulations`
2. Right-click `omnetpp.ini` → **Run As → OMNeT++ Simulation**
3. In the **Run Configuration** dialog:
   - Config name: `General`
   - Leave all defaults → Click **OK**
4. The Qtenv window opens showing the network topology:
   - Blue circles: LoRa end devices
   - Tower icon: Gateway
   - Server icon: Network server

**Controls in Qtenv:**
- `▶` (green arrow): Run at normal speed with animation
- `⏩` (fast-forward): Express mode — much faster, less animation
- Pause/Step for debugging

### 5.3 Verify Simulation Is Working

Expected behavior during run:
- Nodes transmit packets (animated lines between nodes and gateway)
- Gateway forwards to Network Server
- Console shows packet delivery counts
- No red error popups

**Console output (Cmdenv mode) shows:**
```
** Event #1234  t=3600  Elapsed: 5.2s (26%)
Statistic: loRaNodes[0].app[0].LoRa_AppLayerToMAC = 120
Statistic: LoRaGW[0].Lora_PacketForwarder.LoRaGWForwarded = 110
Statistic: networkServer.packetDelivered = 108
Simulation completed (total time = ...) with result: Completed normally.
```

### 5.4 Run the ADR Scenario (Week 1 Baseline)

1. Right-click `simulations/examples/n1000-gw1-ADR.ini` → **Run As → OMNeT++ Simulation**
2. In Run Configuration, select config `General` → OK
3. The ADR network server evaluates and adjusts spreading factors dynamically

**Difference with ADR enabled:**
- `**.networkServer.**.evaluateADRinServer = true`
- `**.evaluateADRinNode = true`
- Network server sends MAC commands (LinkADRReq) to adjust SF/TP
- Nodes respond (LinkADRAns)

### 5.5 Command-Line Run (Alternative)

Inside the MinGW shell:
```bash
cd /c/omnetpp/samples/flora/simulations

# Run default scenario in console mode
../src/flora -u Cmdenv -c General omnetpp.ini

# Run ADR scenario
../src/flora -u Cmdenv -c General examples/n1000-gw1-ADR.ini

# Run with output redirect
../src/flora -u Cmdenv omnetpp.ini > output.log 2>&1
```

---

## Phase 6 — Collecting Results and Metrics

### 6.1 Result Files Location

```
C:\omnetpp\samples\flora\simulations\results\
├── General-0.sca     ← Scalar results (final values per run)
├── General-0.vec     ← Vector results (time-series per run)
└── General-0.vci     ← Vector index (fast lookup into .vec)
```

### 6.2 Open Analysis Tool in IDE

1. Double-click `simulations/General-avg.anf` in Project Explorer
2. The **Analysis Tool** opens with pre-configured charts showing:
   - PDR (Packet Delivery Ratio) vs time or node count
   - Spreading Factor distribution (SF7 through SF12)
   - Energy consumption per node
   - RSSI histograms at the gateway

### 6.3 Key Metrics and Their Signals

| Metric | Signal Name | Location |
|--------|------------|---------|
| Packet Delivery Ratio | `packetDelivered` / `LoRa_AppLayerToMAC` | networkServer, nodes |
| Sent by nodes | `LoRa_AppLayerToMAC` | each LoRaNode app |
| Forwarded by GW | `LoRaGWForwarded` | LoRaGW.packetForwarder |
| Delivered to server | `packetDelivered` | networkServer |
| SF per node | `SF` (scalar, logged at end) | LoRaNode MAC |
| Energy consumed | `energyConsumption` (in Joules) | LoRaEnergyConsumer |

**Calculate PDR:**
```
PDR = packetDelivered / (LoRa_AppLayerToMAC * numGateways)
```

### 6.4 Export to CSV

In the Analysis Tool:
1. Right-click any chart → **Export Data → CSV...**
2. Or from the **Results** tab: select scalars/vectors → right-click → **Export to CSV**

CSV export path (default):
```
C:\omnetpp\samples\flora\simulations\results\
```

To export from command line using `opp_scavetool`:
```bash
cd /c/omnetpp/samples/flora/simulations/results

# Export all scalars to CSV
opp_scavetool export -f General-0.sca -o results_scalars.csv

# Export specific vector with filter
opp_scavetool export -f General-0.vec \
  --filter "name(packetDelivered)" \
  -o pdr_vector.csv
```

---

## Project Explorer Final State

After successful setup, Project Explorer should show:

```
Project Explorer
├── flora                         [OMNeT++ Project]
│   ├── src/
│   │   ├── LoRa/
│   │   ├── LoRaApp/
│   │   ├── LoRaEnergyModules/
│   │   └── LoRaPhy/
│   ├── simulations/
│   │   ├── omnetpp.ini
│   │   ├── General-avg.anf
│   │   └── examples/
│   │       ├── n1000-gw1-ADR.ini   ← Week 1 ADR baseline
│   │       └── n1000-gw1-noADR.ini
│   └── [Referenced: inet4.4]
│
└── inet4.4                       [OMNeT++ Project]
    ├── src/
    ├── examples/
    └── tutorials/
```

---

## Success Checklist

```
[ ] OMNeT++ 6.0.3 extracted to C:\omnetpp
[ ] OMNeT++ builds successfully (opp_run --version works in MinGW shell)
[ ] INET 4.4.1 extracted to C:\omnetpp\samples\inet4.4
[ ] INET imported and built in IDE (0 errors)
[ ] FLoRa v1.1.0 in C:\omnetpp\samples\flora
[ ] FLoRa imported and Project References points to inet4.4
[ ] FLoRa builds (0 errors, flora.exe exists)
[ ] simulations/omnetpp.ini runs → Qtenv animation shows nodes+gateway
[ ] Simulation completes with "Completed normally" in console
[ ] General-avg.anf opens with result charts
[ ] CSV export works from Analysis Tool
```

**→ FLoRa READY: Run LoRaWAN ADR for Week 1 baseline using `examples/n1000-gw1-ADR.ini`**
