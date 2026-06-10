# ADR-Secure — Contributing Guide

Thank you for your interest in contributing to this research project!

## Getting Started

1. **Fork** this repository on GitHub
2. **Clone** your fork:
   ```bash
   git clone https://github.com/<your-username>/adr-secure-lorawan.git
   cd adr-secure-lorawan
   ```
3. Set up the environment following [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md)
4. Build FLoRa and verify with a baseline simulation

## Development Workflow

```
main         ← stable, paper-reproducible results
develop      ← integration branch
feature/xyz  ← your feature branch
```

Please submit PRs to `develop`, not directly to `main`.

## Code Standards

- **C++ (FLoRa modules):** Follow the existing OMNeT++ module style
  - Use `EV <<` for debug output
  - Respect the LGPL-3.0 header comment block in all source files
  - Parameter names: `camelCase` (matching FLoRa conventions)

- **Python (scripts/):** PEP 8, with type hints where practical
  - All scripts must run without error when no result CSV files are present
  - Use `argparse` for CLI arguments

- **INI configs:** Follow the naming convention:
  ```
  n<nodes>-gw<num>-K<attackers>-<mode>-<variant>.ini
  ```

## Bug Reports

Please include:
- OMNeT++ version, INET version, OS
- The exact `.ini` file and run command
- Full error output or the relevant `.log` file

## Feature Requests

Prioritised areas for contribution:
- [ ] Multi-channel LoRaWAN model
- [ ] Mobile node support
- [ ] Adaptive attacker strategies (varying δ per node/time)
- [ ] Hardware testbed validation interface
- [ ] Integration with Chirpstack / TTN for real NS testing

## License

All contributions must be compatible with **LGPL-3.0**.
