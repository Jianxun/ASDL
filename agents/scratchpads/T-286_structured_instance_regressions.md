# T-286 Structured Instance Regression Coverage

## Goal
Add explicit regression tests that keep structured instance lowering and netlist behavior aligned with inline shorthand semantics.

## Notes
- Add one positive structured-instance e2e path.
- Add one malformed structured-instance path that must emit diagnostics, not exceptions.

## Verify
- `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/cli/test_netlist.py -v`
