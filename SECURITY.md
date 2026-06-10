# Security Policy

## Supported Versions

This is a research prototype. Security patches are applied to the `main` branch only.

## Reporting a Vulnerability

This project studies **intentional vulnerabilities in LoRaWAN ADR** for academic purposes.

If you discover a security vulnerability in the **simulation framework code itself** (e.g., unsafe subprocess execution, path traversal in scripts), please report it via GitHub Issues with the label `security`.

**Do NOT** use this code to attack production LoRaWAN networks. The SNR-inflation attack implemented here is for controlled simulation research only. Deploying it against real networks is illegal.

## Responsible Disclosure

- The attack implemented in `PacketForwarder.cc` (`isMalicious=true`) is **only effective inside the OMNeT++ simulator**
- No real LoRaWAN gateway firmware is distributed here
- All experiments require explicit INI configuration — there is no "auto-attack" mode

## Threat Model Scope

The security contribution of this work is the **ADR-Secure defense**, which protects against SNR-inflation attacks at the Network Server level. See [`paper/main.tex`](paper/main.tex) Section III for the full threat model.
