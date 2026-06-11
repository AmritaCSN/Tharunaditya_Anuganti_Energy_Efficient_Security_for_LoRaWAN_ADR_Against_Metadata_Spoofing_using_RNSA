# Energy Efficient Security for LoRaWAN ADR Against Metadata Spoofing using Robust Network Server aggregation
# ADR-Secure: Byzantine-Resilient Adaptive Data-Rate Control for LoRaWAN 

[![OMNeT++ 6.0.3](https://img.shields.io/badge/OMNeT%2B%2B-6.0.3-green.svg)](https://omnetpp.org)
[![INET 4.4.1](https://img.shields.io/badge/INET-4.4.1-orange.svg)](https://inet.omnetpp.org)
[![FLoRa v1.1.0](https://img.shields.io/badge/FLoRa-v1.1.0-purple.svg)](https://flora.aalto.fi)
[![License: LGPL-3.0](https://img.shields.io/badge/License-LGPL%203.0-blue.svg)](flora/LICENSE.md)

**Project code:** AM.SC.P2CSN24017  
**Author:** Tharunaditya Anuganti  
**Affiliation:** Amrita Center for Cybersecurity Systems and Networks, Amrita Vishwa Vidyapeetham

---

## What is this?

LoRaWAN's Adaptive Data-Rate (ADR) algorithm adjusts the Spreading Factor (SF) of each device based on signal quality reports from gateways. The problem is that ADR trusts those reports without any verification — a compromised gateway can lie about the SNR it measured, and the Network Server has no way to tell.

This project quantifies that attack and proposes a practical fix.

**The attack:** A malicious gateway inflates the SNR it reports (e.g., adds +20 dB). The Network Server thinks the channel is excellent and pushes nodes to SF7. But the real channel needs SF9 or SF11, so those SF7 packets fail to decode at the receiver. The device keeps transmitting, the gateway keeps forwarding, but the Network Server never receives the application data. PDR (Packet Delivery Ratio) drops from ~87% to ~44%.

**The fix (ADR-Secure):** Instead of trusting the single best-SNR gateway, the Network Server computes the **median** over all gateways that received the uplink. The median is Byzantine-fault-tolerant: a strict minority of attackers cannot shift it beyond the range of honest values. Additionally, when only one gateway forwards a packet, ADR-Secure skips that packet's ADR history update rather than trusting an unverifiable single source.

This fix is a ~30-line change to one function in `NetworkServerApp.cc`, requires no gateway or device modifications, and is activated with a single INI parameter.

---

## Results

| Scenario | Gateways | Malicious GWs | SNR Offset | PDR | Avg SF |
|----------|----------|---------------|-----------|-----|--------|
| Baseline | 1 | 0 | — | **87.3%** | 7.47 |
| Attack | 3 | K=1 | +20 dB | 44.5% | 7.00 |
| ADR-Secure | 3 | K=1 | +20 dB | **91.9%** | 8.06 |
| Attack | 3 | K=2 | +20 dB | 77.9% | 7.00 |
| ADR-Secure | 3 | K=2 | +20 dB | **92.0%** | ~8.0 |

All numbers are averaged over 5 independent simulation runs (different random seeds). The K=2 result at 92% is explained by the single-source abstention policy, which operates independently of the BFT median and dominates when most packets reach only one gateway.

---

## Repository Structure

```
.
├── flora/                          # Modified FLoRa v1.1.0
│   ├── src/
│   │   ├── LoRa/
│   │   │   ├── NetworkServerApp.cc  ← ADR-Secure implementation
│   │   │   ├── PacketForwarder.cc   ← SNR-inflation attack implementation
│   │   │   └── ...
│   │   ├── LoRaApp/
│   │   ├── LoRaPhy/
│   │   ├── LoRaEnergyModules/
│   │   └── LoraNode/
│   └── simulations/
│       └── examples/               ← 30 experiment INI configs
│
├── scripts/
│   ├── analyze_results.py          ← Export SCA files, generate figures and result summaries
│   ├── run_matrix.ps1              ← Windows: run all experiments sequentially
│   ├── gen_uniform_ini.py          ← Uniform topology INI generator
│   ├── gen_scaleup_ini.py          ← Scalability INI generator
│   ├── setup_env.ps1               ← Environment validator (Windows)
│   ├── verify_build.ps1            ← Post-build verification
│   └── build_all.sh                ← Linux/WSL build helper
│
├── results/
│   └── figures/                    ← Generated plots (PDR vs K, SF distribution, scalability, etc.)
│
└── docs/
    ├── PROJECT_EXPLANATION.md      ← Full write-up of attack, defense, and results
    ├── SETUP_GUIDE.md              ← Installation instructions
    ├── SIMULATION_GUIDE.md         ← How to run experiments
    ├── TROUBLESHOOTING.md          ← Known issues and fixes
    └── VERSION_NOTES.md            ← Verified version compatibility matrix
```

---

## Getting Started

### Prerequisites

You need three things:
- **OMNeT++ 6.0.3** — the simulation engine ([download](https://omnetpp.org/download/old))
- **INET 4.4.1** — the network framework FLoRa depends on ([download](https://github.com/inet-framework/inet/releases/tag/v4.4.1))
- **Python 3.x** with `matplotlib` and `numpy` for the analysis scripts

> INET 4.5.x and above are not compatible with FLoRa. On Windows, use the MinGW shell that comes bundled with OMNeT++ for all build commands — regular PowerShell will not work.

### Building

```bash
# In the OMNeT++ MinGW shell:
cd /c/path/to/this-repo/flora
make makefiles INET_PROJ=/c/path/to/inet4.4
make -j4 MODE=release
```

See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for the full step-by-step installation.

### Running an Experiment

```bash
cd flora/simulations

# Baseline (no attack):
../src/flora -u Cmdenv examples/n100-gw1.ini

# Attack — K=1 malicious gateway, +20 dB SNR inflation:
../src/flora -u Cmdenv examples/n100-gw3-K1-attack.ini

# Defense — ADR-Secure active:
../src/flora -u Cmdenv examples/n100-gw3-K1-defense.ini
```

### Analysing Results

```bash
# Export SCA files to CSV and generate figures + tables:
python scripts/analyze_results.py --export

# If CSV files are already present:
python scripts/analyze_results.py
```

Figures go to `results/figures/`.

---

## Key Code Changes

### Attack: `flora/src/LoRa/PacketForwarder.cc`

Three new parameters added to the `PacketForwarder` NED module:

```cpp
isMalicious     // bool  — enable attack mode
snrOffset       // double — fixed dB inflation
snrOffsetMode   // string — "fixed", "step" (ramp), or "random"
```

When `isMalicious = true`, the forwarder multiplies the measured SNIR in linear scale before forwarding to the Network Server:

```cpp
frame->setSNIR(frame->getSNIR() * std::pow(10.0, effectiveSnrOffset / 10.0));
```

### Defense: `flora/src/LoRa/NetworkServerApp.cc`

In `evaluateADR()`, before any per-node history update:

```cpp
if (adrMethod == "secure" && allGateways.size() >= 2) {
    // BFT median — Byzantine-robust for K < N/2 attackers
    std::sort(sorted_lin.begin(), sorted_lin.end());
    SNIRinGW = sorted_lin[N / 2];
    bft_applied = true;
}

// Single-source abstention
if (do_abstain && !bft_applied) {
    break;  // skip ADR history update — cannot verify single GW
}
```

Activated by: `**.networkServer.app[0].adrMethod = "secure"` in the INI file.

---

## Simulation Configurations

The `flora/simulations/examples/` directory contains 30 INI configs:

| Pattern | Description |
|---------|-------------|
| `n100-gw1.ini` | Clean baseline, 1 GW |
| `n100-gw2-attack/defense.ini` | 2 GW, K=1 |
| `n100-gw3-K1-attack/defense.ini` | 3 GW, K=1 |
| `n100-gw3-K2-attack/defense.ini` | 3 GW, K=2 (BFT bound test) |
| `n100-gw4-K1-*.ini` | 4 GW, K=1 |
| `n100-gw5-K2/K3-*.ini` | 5 GW, K=2/K=3 |
| `n*00-3gw-*.ini` | Scalability: N=200, 500, 1000 |
| `n100-3gw-uniform.ini` | Uniform topology robustness |
| `n100-gw3-K1-*-only.ini` | Ablation: median-only, abstain-only |
| `n100-gw3-K1-adaptive-*.ini` | Adaptive attacker (step/random δ) |

Each attack/defense pair runs with `${attackOffset = 20.0, 40.0}` and `repeat = 5`, giving 10 runs per config file.

---

## Dependencies and Licenses

This repository contains a modified version of **FLoRa v1.1.0**, which is:
- © 2019 M. Slabicki, G. Premsankar, M. Di Francesco
- Licensed under **GNU Lesser General Public License v3.0**
- Original: [github.com/florasim/flora](https://github.com/florasim/flora)

All modifications in this repository are released under the same LGPL-3.0 license. See [flora/LICENSE.md](flora/LICENSE.md).

FLoRa depends on INET Framework ([inet-framework/inet](https://github.com/inet-framework/inet)) and OMNeT++ ([omnetpp.org](https://omnetpp.org)), both used under their respective open-source licenses.

---

## Citing This Work

```bibtex
@inproceedings{anuganti2026adrsecure,
  author    = {Tharunaditya Anuganti},
  title     = {{ADR-Secure}: Byzantine-Resilient Adaptive Data-Rate Control for {LoRaWAN}},
  year      = {2026},
  institution = {Amrita Center for Cybersecurity Systems and Networks,
                 Amrita Vishwa Vidyapeetham, India}
}
```
