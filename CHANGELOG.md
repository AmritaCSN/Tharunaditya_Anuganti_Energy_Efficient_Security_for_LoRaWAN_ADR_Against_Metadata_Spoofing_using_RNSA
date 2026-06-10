# Changelog

All notable changes to ADR-Secure are documented in this file.

Format: `[Version] - YYYY-MM-DD`

---

## [Unreleased]

### Planned
- Multi-channel LoRaWAN model support
- Mobile node scenarios
- Adaptive attacker (time-varying δ) evaluation

---

## [1.0.0] - 2026-06-10

### Added (Research Contributions)
- **ADR-Secure BFT median defense** in `NetworkServerApp::evaluateADR()`
  - Replaces best-gateway SNR with median over all reporting gateways
  - Byzantine-fault-tolerant for K < N_GW/2 compromised gateways
  - Activated via `adrMethod = "secure"` INI parameter
- **Conservative single-source abstention policy**
  - Skips ADR history update when only one gateway forwarded the uplink
  - Prevents unverifiable single-gateway SNR from poisoning ADR window
- **SNR-inflation attack** in `PacketForwarder::processLoraMACPacket()`
  - New parameters: `isMalicious`, `snrOffset`, `rssiOffset`, `snrOffsetMode`
  - Attack modes: `fixed` (constant δ), `step` (ramp), `random` (uniform noise)
- **33 simulation INI configurations** covering:
  - Baseline: n100-gw1 (K=0)
  - N=100: 2GW/3GW/4GW/5GW attack+defense, K=1,2,3
  - N=200,500,1000: Scalability (3GW, K=1)
  - Uniform topology robustness
  - Ablation studies: `median_only`, `abstain_only` variants

### Added (Infrastructure)
- `scripts/analyze_results.py`: full analysis pipeline
  - Exports SCA → CSV, extracts PDR/SF/energy/collision metrics
  - Generates 6 matplotlib figures (PDF + PNG)
  - Generates 7 LaTeX tables (summary, SF distribution, energy, scalability, uniform)
  - Outputs `results/paper_numbers.txt` for paper patching
  - Computes 95% confidence intervals across 5 seeds
- `scripts/update_paper.py`: auto-patches `paper/main.tex` with real numbers
- `scripts/run_matrix.ps1`: Windows PowerShell runner for all experiments
- `scripts/run_journal_experiments.ps1`: Journal-scale runner
- `scripts/gen_uniform_ini.py`: INI generator for uniform topology
- `scripts/gen_scaleup_ini.py`: INI generator for scalability experiments
- `paper/main.tex`: Full IEEEtran conference paper
- `paper/presentation.tex`: Beamer slide deck (Second Review format)
- Comprehensive documentation: SETUP_GUIDE, SIMULATION_GUIDE, TROUBLESHOOTING, VERSION_NOTES

### Fixed (Bug Log)
| Date | Bug | Fix |
|------|-----|-----|
| Mar 19 | Defense = attack (no effect) | Negative offsets → BFT picks weak honest value → switched to positive (inflation) |
| Mar 20 | Defense still = attack | Nodes at SF7 → honest GWs out of range → `allGateways.size()=1` → BFT never runs; fixed via single-source abstention |
| Mar 20 | `plot_metric_vs_K` empty plots | `offset_filter=-20` default, all offsets now +20 → changed default to +20 |
| Mar 20 | K=1 plot had vertical segment | Both 2GW and 3GW map to K=1 → average same-K values |
| Mar 21 | K2 configs crash exit code 1 | `${attackOffset}` declared twice → GW[2] changed to reference without re-declaration |

---

## [0.1.0] - 2026-03-14 (Week 1 Baseline)

### Added
- Installed OMNeT++ 6.0.3 + INET 4.4.1 on Windows
- Cloned and built FLoRa v1.1.0 from source (`libflora.dll`)
- Ran baseline simulation: 100 nodes, 1 GW, 24h
- Established reference metrics: PDR=87.3%, avg SF=7.47, energy=75.2 mJ/pkt
