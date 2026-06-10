## Summary

<!-- 1-2 sentence description of what this PR does -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature / experiment configuration
- [ ] Documentation update
- [ ] Analysis script improvement
- [ ] Refactoring (no functional change)

## Related Issue

Closes #<!-- issue number -->

## Changes Made

<!-- Bullet list of specific files/functions changed -->

- `flora/src/LoRa/NetworkServerApp.cc`:
- `scripts/`:
- `paper/main.tex`:

## Testing Done

<!-- Describe how you verified the changes work correctly -->

- [ ] Ran baseline simulation and verified PDR ≈ 87%
- [ ] Ran attack simulation and verified PDR drops to ~44%
- [ ] Ran defense simulation and verified PDR recovers to ~92%
- [ ] Ran `python scripts/analyze_results.py` — no errors
- [ ] Checked that figures generate correctly

## Checklist

- [ ] My code follows the project's style conventions
- [ ] I have tested the simulation runs end-to-end
- [ ] I have updated documentation if needed
- [ ] All modified files retain their LGPL-3.0 license header
- [ ] No large binary files or CSV data files are included in the PR
