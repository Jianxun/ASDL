# T-050 Netlist Test Backend Config

## Task summary
- DoD: Make netlist CLI/e2e tests deterministic by writing a temporary backend config and setting `ASDL_BACKEND_CONFIG` in tests; ensure expected netlists align with the test templates and do not rely on repo `config/backends.yaml`.
- Verify: `pytest tests/unit_tests/cli -v && pytest tests/unit_tests/e2e -v`

## Read
- `tests/unit_tests/cli/test_netlist.py`
- `tests/unit_tests/e2e/test_pipeline_mvp.py`
- `src/asdl/emit/backend_config.py`
- `config/backends.yaml`

## Plan
- Add a helper to write a minimal backend config into `tmp_path` for CLI/e2e tests.
- Set `ASDL_BACKEND_CONFIG` in tests (and restore env) to point at the temp config.
- Update expected netlist strings to match the deterministic templates.

## Progress log
- Initialized scratchpad.

## Patch summary
- TBD.

## Verification
- TBD.

## Blockers / Questions
- None.

## Next steps
- Implement deterministic backend config setup in CLI/e2e tests.
