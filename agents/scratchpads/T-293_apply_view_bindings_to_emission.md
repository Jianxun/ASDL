# T-293 - Apply resolved view bindings to netlist emission input

## Goal
Ensure resolved view bindings are applied to emitted instance references before netlist rendering.

## Notes for Executor
- Preserve deterministic sidecar ordering.
- Preserve existing realization-name and duplicate-name disambiguation logic.
- Add regression proving profile differences change emitted refs.

## Verify
- `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/cli/test_netlist.py -k "view and binding" -v`
