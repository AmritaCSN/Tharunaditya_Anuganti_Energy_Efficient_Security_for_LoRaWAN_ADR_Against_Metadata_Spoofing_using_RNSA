# VERSION_NOTES.md
# Verified Version Compatibility and Research Notes
# Last updated: March 2026

---

## Confirmed Version Matrix

| Component | Version | Source | Notes |
|-----------|---------|--------|-------|
| OMNeT++ | 6.0.3 | github.com/omnetpp/omnetpp | Feb 28, 2024 release |
| INET | **4.4.1** | github.com/inet-framework/inet | Jul 27, 2022 — fixes Windows linker bugs |
| INET | 4.4.2 | github.com/inet-framework/inet | Aug 7, 2024 — also compatible |
| FLoRa | **1.1.0** | github.com/florasim/flora | Jun 9, 2022 — targets INET 4.4.0+ |

---

## Correction: INET 4.4.3 Does NOT Exist

**INET 4.4.3 does NOT exist.** The 4.4.x series ends at 4.4.2.

- 4.4.0 → May 2022
- 4.4.1 → July 2022 (Windows duplicate-symbol fix)
- 4.4.2 → August 2024 (OMNeT++ 6.1 compat fix)
- ~~4.4.3~~ → Does not exist (GitHub returns 404)

Use 4.4.1 (safest for Windows) or 4.4.2.

---

## Correction: FLoRa Has Only One Branch

`florasim/flora` has only the `master` branch.
There is no `inet4` branch.

Tag history:
- `v1.1.0` — June 9, 2022 — INET 4.4.x, OMNeT++ 6.0 ✓
- `v1.0.0` — April 11, 2021 — INET 4.3.x, OMNeT++ 6.0 pre-release
- `v0.8`   — June 3, 2018 — INET 3.x, OMNeT++ 5.x
- `v0.7.1` — May 17, 2018 — INET 3.x, OMNeT++ 5.x

---

## Why INET 4.4.1 (Not 4.4.0) on Windows

INET 4.4.1 release notes state:
> "Fixed duplicate symbol linker errors on Windows when using template classes as a base class."

This directly addresses the most common FLoRa + Windows build failure:
```
lld-link: error: duplicate symbol: inet::SharingTagSet::setTag(...)
lld-link: error: 1890 duplicate symbols
```

---

## INET 4.5.x / 4.6.x Incompatibility

- **INET 4.5.x**: Introduces breaking API changes (network interfaces, packet filter expressions, signals/statistics). FLoRa has NOT been migrated. GitHub issue #74 for FLoRa ("Version Migration to INET 4.5.2") has no maintainer response.
- **INET 4.6.x**: Requires OMNeT++ 6.2+. Use of INET 4.6 with OMNeT++ 6.0.3 will fail at configuration time.

---

## Simulation File Truth (No "LoRaWAN_ADR" Config)

FLoRa does NOT have a config named "LoRaWAN_ADR". The ADR scenario is:
```
simulations/examples/n1000-gw1-ADR.ini
```

The ini uses `[General]` as its config section name.
ADR is enabled via:
```ini
**.networkServer.**.evaluateADRinServer = true
**.evaluateADRinNode = true
```

There is no "3GW/50nodes" default scenario — closest is n1000-gw2.ini (2 gateways, 1000 nodes).

---

## Windows MinGW Environment Requirement

OMNeT++ on Windows uses an **exclusive MinGW/MSYS** build environment.
- MSVC is **not supported**
- Regular PowerShell/cmd.exe will NOT have the correct PATH or tools
- All `make`, `gcc`, `configure`, and `git` commands must run inside `mingwenv.cmd`

The bundled toolchain is: MinGW-w64 + LLVM/lld

---

## Path Recommendations

To avoid Windows 260-char MAX_PATH problems:
```
C:\omnetpp\              ← OMNeT++ root (SHORT path)
C:\omnetpp\samples\      ← workspace (set as IDE workspace directory)
C:\omnetpp\samples\inet4.4\
C:\omnetpp\samples\flora\
```

Do NOT use paths like:
```
C:\Users\Username\Documents\Projects\Research\LoRaWAN\...   ← too deep
```

---

## OMNeT++ Version Alternatives

If you move to OMNeT++ 6.1.x or 6.2.x:
- INET 4.4.2 added OMNeT++ 6.1 compatibility
- FLoRa 1.1.0 has not been formally tested with OMNeT++ 6.1+ by maintainers
- Users have reported FLoRa working with OMNeT++ 6.1 + INET 4.4.2 (unofficially)
- OMNeT++ 6.3.0 (latest as of March 2026) compatibility with FLoRa 1.1.0 is unknown

For guaranteed support: use OMNeT++ 6.0.3 + INET 4.4.1 + FLoRa 1.1.0.

---

## Official Resources

- FLoRa project page: https://flora.aalto.fi
- FLoRa GitHub: https://github.com/florasim/flora
- FLoRa Issues: https://github.com/florasim/flora/issues
- INET Framework: https://github.com/inet-framework/inet
- OMNeT++ Downloads: https://omnetpp.org/download/
- OMNeT++ Old Downloads: https://omnetpp.org/download/old
