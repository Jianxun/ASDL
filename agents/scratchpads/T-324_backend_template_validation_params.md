# T-324 Scratchpad

## Goal
Finalize backend template validation and sample backend coverage for parameterized subckt headers/calls.

## Reuse audit checklist
- Reuse system device required/allowed placeholder validation maps.
- Reuse existing backend config loading/validation test scaffolding.
- Reuse render regression harness for backend-specific output assertions.

## Expected behavior
- Required template validation covers parameterized system templates.
- `examples/config/backends.yaml` remains authoritative for backend syntax quirks.
- Regression tests guard ngspice/xyce/spectre parameterized forms.

## Verify
- `./venv/bin/pytest tests/unit_tests/emit/test_backend_config.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`
