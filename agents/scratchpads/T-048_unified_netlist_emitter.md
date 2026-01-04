# T-048 Unified netlist emitter rewrite

## Goal
- Replace `emit_ngspice` with a unified netlist emitter that selects backends via `--backend`.
- Split verification from rendering and keep backend-specific checks in a dedicated pass.

## Scope
- New emitter module/package under `src/asdl/emit/`.
- Remove `src/asdl/emit/ngspice.py` and `emit_ngspice` import surface.
- Add CLI `--backend` with default `sim.ngspice`.
- Backend config schema is `extension`, `comment_prefix`, `templates` (verbatim `extension`).
- Top module emits no wrapper when `top_as_subckt` is false.

## File touch list (expected)
- `src/asdl/emit/` (new emitter + verify pass)
- `src/asdl/emit/__init__.py`
- `src/asdl/cli/__init__.py`
- `config/backends.yaml`
- `tests/unit_tests/emit/test_backend_config.py`
- `tests/unit_tests/netlist/`
- `tests/unit_tests/cli/test_netlist.py`
- `tests/unit_tests/e2e/test_pipeline_mvp.py`

## Notes
- Backend names should be updated to `sim.ngspice` in tests and fixtures.
- Output extension should come from backend config; CLI default output path uses that.
