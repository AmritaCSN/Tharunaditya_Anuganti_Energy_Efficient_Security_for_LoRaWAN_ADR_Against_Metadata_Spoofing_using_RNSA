# Simulation Guide: Running LoRaWAN Scenarios with FLoRa

---

## Available Simulation Configurations

### Default Scenario — `simulations/omnetpp.ini` [General]

```ini
# What the General config contains:
[General]
network = flora.simulations.LoRaNetworkTest
sim-time-limit = 1d          # 24-hour simulation
warmup-period = 0s

# Network parameters
**.numNodes = 1               # Single node (minimal test)
**.numGateways = 1

# LoRa PHY
**.loRaTransmitter[*].initialLoRaSF = 12
**.loRaTransmitter[*].initialLoRaTP = 14dBm
**.loRaTransmitter[*].initialLoRaBW = 125kHz
**.loRaTransmitter[*].initialLoRaCR = 4

# Application
**.LoRaNodeApp[0].sendPacketsCnt = 0   # 0 = unlimited
**.LoRaNodeApp[0].timeToFirstPacket = uniform(0s, 30s)
**.LoRaNodeApp[0].timeToNextPacket = exponential(300s)  # ~12 per hour
```

Run this first to verify the setup works.

---

## ADR Scenario — Week 1 Baseline

### File: `simulations/examples/n1000-gw1-ADR.ini`

This is your primary research scenario. Key parameters:

```ini
[General]
network = flora.simulations.LoRaNetworkTest
sim-time-limit = 7d           # 7 days

**.numNodes = 1000
**.numGateways = 1

# ADR enabled on network server
**.networkServer.**.evaluateADRinServer = true
# ADR enabled on nodes (they respond to ADR commands)
**.evaluateADRinNode = true

# Initial spreading factor (ADR will adapt this)
**.loRaTransmitter[*].initialLoRaSF = 12

# Network server ADR parameters
**.networkServer.adrMethod = "sf"
```

### What ADR Does
The Adaptive Data Rate (ADR) algorithm:
1. **Network Server** monitors SNR history per node (last N packets)
2. Calculates optimal SF (Spreading Factor) and TP (Transmit Power)
3. Sends `LinkADRReq` MAC commands to node
4. **Node** responds with `LinkADRAns` and adjusts radio parameters
5. Result: nodes close to gateway use SF7 (fast), distant nodes use SF12 (far reach)

### Expected ADR Behavior
- Simulation start: all 1000 nodes at SF12 (default)
- After ~20 packets per node: ADR kicks in
- Distribution shifts toward lower SFs (SF7-SF9) for most nodes
- Energy consumption drops significantly for close-in nodes
- PDR may improve or stabilize as collision rate decreases

---

## Scenario Comparison Matrix

| Scenario | Nodes | GW | ADR | Duration | Use Case |
|----------|-------|----|-----|----------|---------|
| `omnetpp.ini` General | 1 | 1 | Off | 1 day | Verify setup |
| `n100-gw1.ini` | 100 | 1 | Off | configurable | Small network baseline |
| **`n1000-gw1-ADR.ini`** | **1000** | **1** | **On** | **7 days** | **Week 1 ADR baseline** |
| `n1000-gw1-noADR.ini` | 1000 | 1 | Off | 7 days | ADR comparison (control) |
| `n1000-gw2.ini` | 1000 | 2 | Off | 7 days | Multi-gateway coverage |

---

## Running Simulations

### From IDE (Graphical)

**Step 1: Open the ini file**
```
Project Explorer → flora → simulations → examples → n1000-gw1-ADR.ini
```
Right-click the file → **Run As → OMNeT++ Simulation**

**Step 2: Run Configuration**
- Config name: `General` (unless the ini defines named configs)
- Sim time limit: leave default (from ini)
- Number of runs: 1 (for baseline)
- Click **OK**

**Step 3: Qtenv controls**
| Button | Action |
|--------|--------|
| ▶ Run | Animated run (slow) |
| ⏩ Fast | Express run (100x faster, less visual) |
| ⏸ Pause | Pause simulation |
| ⏹ Stop | Stop and collect results |
| ⏭ Step | Single event step |

For 1000 nodes over 7 days, use **Express mode**.

### From Command Line

```bash
cd /c/omnetpp/samples/flora/simulations

# Run ADR scenario, console mode (fastest)
../src/flora -u Cmdenv -c General examples/n1000-gw1-ADR.ini

# Run with specific simulation time
../src/flora -u Cmdenv -c General \
  --sim-time-limit=3d examples/n1000-gw1-ADR.ini

# Run multiple repetitions (for statistical analysis)
../src/flora -u Cmdenv -c General \
  -r 0,1,2,3,4 examples/n1000-gw1-ADR.ini

# Run in parallel (5 repetitions across 4 cores)
opp_runall -j4 ../src/flora -u Cmdenv -c General \
  examples/n1000-gw1-ADR.ini
```

### Expected Console Output Progress

```
** Event #100000  t=86400 (1d 0h 0m 0s)  Elapsed: 12.3s (14.3%)
** Event #200000  t=172800 (2d 0h 0m 0s)  Elapsed: 24.1s (28.6%)
...
** Event #700000  t=604800 (7d 0h 0m 0s)  Elapsed: 85.2s (100%)
Simulation completed (cpu_time=85.2s, realtime=85.2s)
```

Typical 7-day ADR run: **1-5 minutes** in Cmdenv on modern hardware.

---

## Collecting and Analyzing Results

### Result Files Generated

```
simulations/results/
├── General-0.sca          ← Scalar results (summary statistics per run)
├── General-0.vec          ← Vector results (time-series data)
└── General-0.vci          ← Vector index (for fast vec lookups)
```

With multiple runs (repetitions), numbered `.sca` and `.vec` files are created.

### Key Metrics to Collect

#### Packet Delivery Ratio (PDR)
```
PDR = Total Delivered / Total Sent
```

From `.sca` file, look for:
- `"packetDelivered:count"` in `networkServer` module
- `"LoRa_AppLayerToMAC:count"` in each node's app module

#### Spreading Factor Distribution
After ADR convergence:
- `"SF:last"` scalar per node (SF7=1 ... SF12=6 mapping)
- Or vector `"SF:vector"` to see SF evolution over time

#### Energy Consumption
- `"energyConsumption:sum"` in `LoRaEnergyConsumer` per node
- Units: Joules

#### Collision / Interference
- `"lostPackets:count"` at gateway level
- `"receivedRSSI:mean"` and `"receivedSNIR:mean"` for channel quality

### Load in Analysis Tool

1. Double-click `simulations/General-avg.anf` in Project Explorer
2. The file opens with pre-configured charts
3. Add new charts: **Add Chart → Bar Chart / Line Chart / Histogram**

### Export to CSV

#### Method 1: From IDE
1. In Analysis Tool, click the **Results** tab
2. Select scalars or vectors you want
3. Right-click → **Export to CSV**

#### Method 2: opp_scavetool (command line)

```bash
cd /c/omnetpp/samples/flora/simulations/results

# List all available result names
opp_scavetool query -l General-0.sca

# Export all scalars
opp_scavetool export General-0.sca -o all_scalars.csv

# Export specific metric across all runs
opp_scavetool export General-*.sca \
  --filter "name(packetDelivered) AND module(networkServer)" \
  -o pdr_results.csv

# Export SF distribution
opp_scavetool export General-0.sca \
  --filter "name(SF*)" \
  -o sf_distribution.csv

# Export energy consumption
opp_scavetool export General-0.sca \
  --filter "name(*energyConsumption*)" \
  -o energy_results.csv

# Export time-series vector
opp_scavetool export General-0.vec \
  --filter "name(SF:vector)" \
  -o sf_timeseries.csv
```

### CSV Output Structure

```csv
run,module,name,value
General-0-0,networkServer,packetDelivered:count,9823
General-0-0,loRaNodes[0].LoRaNodeApp[0],LoRa_AppLayerToMAC:count,12
General-0-0,loRaNodes[0].energyConsumer,energyConsumption:last,0.00234
...
```

---

## Understanding FLoRa's LoRaWAN Architecture

```
[LoRa End Device]          [LoRa Gateway]          [Network Server]
    LoRaNodeApp               LoRaGW                  NetworkServer
        |                       |                           |
    LoRaMAC                PacketForwarder          (ADR algorithm here)
        |                       |                           |
    LoRaRadio              LoRaGWMac                        |
        |                       |                           |
    LoRaTransmitter             |                           |
        └──── LoRaMedium ───────┘                           |
                                └────── BackhauldMedium ────┘
```

### PHY Parameters You Can Tune

In `omnetpp.ini` or scenario ini files:

```ini
# Spreading Factor (7-12, lower = faster + shorter range)
**.loRaTransmitter[*].initialLoRaSF = 12

# Transmit Power in dBm (2-14 for EU868)
**.loRaTransmitter[*].initialLoRaTP = 14dBm

# Bandwidth (125kHz standard for EU868)
**.loRaTransmitter[*].initialLoRaBW = 125kHz

# Coding Rate (4 = 4/8, default)
**.loRaTransmitter[*].initialLoRaCR = 4

# Center frequency  
**.loRaTransmitter[*].initialLoRaCF = 868MHz

# Path loss exponent (alpha in log-distance model)
**.LoRaMedium.pathLossModel.alpha = 3.5

# Enable/disable ADR
**.networkServer.**.evaluateADRinServer = true
**.evaluateADRinNode = true

# Node deployment area
**.deploymentRadius = 250m   # radius from gateway
```

---

## Running Week 1 Baseline Experiment

### Experimental Setup

For your Week 1 ADR baseline comparison:

**Run 1: ADR Enabled**
```bash
../src/flora -u Cmdenv -c General \
  examples/n1000-gw1-ADR.ini \
  -r 0,1,2
# 3 repetitions with different random seeds
```

**Run 2: ADR Disabled (Control)**
```bash
../src/flora -u Cmdenv -c General \
  examples/n1000-gw1-noADR.ini \
  -r 0,1,2
```

**Collect combined CSV:**
```bash
opp_scavetool export \
  results/General-*.sca \
  --filter "name(packetDelivered) OR name(LoRa_AppLayerToMAC) OR name(*energyConsumption*) OR name(SF*)" \
  -o week1_baseline.csv
```

### Key Results to Report

1. **PDR**: `packetDelivered / (numNodes * sentPackets)` — target >90% with ADR
2. **Average SF**: Mean SF across all nodes at end of simulation
3. **Energy per packet**: `energyConsumption / packetsDelivered` per node
4. **SF distribution**: Histogram of SF7-SF12 at end of 7-day simulation
5. **PDR over time**: Vector showing PDR improvement as ADR adapts

---

## Quick Reference: LoRa PHY — SF vs Performance

| SF | Bit Rate | Range | Airtime (25B payload) | Collision Risk |
|----|---------|-------|----------------------|----------------|
| SF7 | 5470 bps | ~2 km | 56 ms | Low |
| SF8 | 3125 bps | ~4 km | 103 ms | Low |
| SF9 | 1757 bps | ~6 km | 185 ms | Medium |
| SF10 | 980 bps | ~8 km | 370 ms | Medium |
| SF11 | 537 bps | ~11 km | 741 ms | High |
| SF12 | 293 bps | ~15 km | 1319 ms | Very High |

ADR optimization: nodes that can use SF7 (close to gateway) should — this reduces channel occupancy and collision probability for all other nodes.
