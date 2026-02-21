# T-283 - module variables end-to-end coverage

## Task summary
- Add regression tests proving module-variable substitution in netlist output.
- Add executable diagnostics coverage for `IR-012` and `IR-013`.

## Verify
- `./venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py tests/unit_tests/cli/test_netlist.py -v`
