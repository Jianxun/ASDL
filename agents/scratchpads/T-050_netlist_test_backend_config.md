# T-050 Netlist Test Backend Config

## Task summary
- DoD: Make netlist CLI/e2e tests deterministic by writing a temporary backend config and setting `ASDL_BACKEND_CONFIG` in tests; ensure expected netlists align with the test templates and do not rely on repo `config/backends.yaml`.
- Verify: `pytest tests/unit_tests/cli -v && pytest tests/unit_tests/e2e -v`

## Read
- `tests/unit_tests/cli/test_netlist.py`
- `tests/unit_tests/e2e/test_pipeline_mvp.py`
- `src/asdl/cli/__init__.py`
- `src/asdl/emit/backend_config.py`
- `src/asdl/emit/netlist/api.py`
- `src/asdl/emit/netlist/render.py`
- `src/asdl/emit/netlist/templates.py`
- `config/backends.yaml`

## Plan
- Add a helper to write a minimal backend config into `tmp_path` for CLI/e2e tests.
- Set `ASDL_BACKEND_CONFIG` in tests (and restore env) to point at the temp config.
- Update expected netlist strings to match the deterministic templates.

## Progress log
- Initialized scratchpad.
- Reviewed issue #44 and netlist emission/template handling.
- Added per-test backend config helpers + env setup for CLI and e2e tests.
- Ran CLI and e2e pytest targets (see Verification).

## Patch summary
- `tests/unit_tests/cli/test_netlist.py`: write temp backend config + set `ASDL_BACKEND_CONFIG` fixture for CLI tests.
- `tests/unit_tests/e2e/test_pipeline_mvp.py`: add temp backend config fixture to make e2e netlist emission deterministic.

## Verification
- `venv/bin/pytest tests/unit_tests/cli -v`
- `venv/bin/pytest tests/unit_tests/e2e -v`

## Status request
- Done.

## Blockers / Questions
- None.

## Next steps
- Push branch and open PR once ready.
