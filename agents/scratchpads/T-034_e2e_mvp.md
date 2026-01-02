# T-034 - End-to-End MVP Pipeline Test

## Goal
Add an end-to-end MVP test covering AST -> NFIR -> IFIR -> ngspice emission.

## DoD
- Test parses MVP YAML, converts through NFIR/IFIR, and emits ngspice netlist.
- Output is deterministic and respects top handling rules.
- Test uses the MVP specs as the source of truth for expected output.

## Files likely touched
- `tests/unit_tests/e2e/`
- `tests/fixtures/` (if needed)

## Verify
- `pytest tests/unit_tests/e2e`
