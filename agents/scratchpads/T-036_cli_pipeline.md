# T-036 - CLI Netlist via MVP Pipeline

## Goal
Implement `asdlc netlist` to run the MVP pipeline and emit ngspice output.

## DoD
- `asdlc netlist <file.asdl>` uses `src/asdl/ir/pipeline.py` (no direct converter calls).
- Supports `-o/--output`, `--verify/--no-verify`, and `--top-as-subckt`.
- Diagnostics use shared contract and are deterministic; exit code is 1 on error diagnostics.
- Behavior aligns with `docs/specs_mvp/spec_cli_mvp.md`.
- CLI tests cover success and error cases.

## Files likely touched
- `src/asdl/cli/`
- `src/asdl/ir/pipeline.py`
- `docs/specs_mvp/spec_cli_mvp.md`
- `tests/unit_tests/cli/`

## Verify
- `pytest tests/unit_tests/cli`
