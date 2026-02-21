# T-282 - module variable substitution and diagnostics

## Task summary
- Implement `{var}` substitution for instance parameter values.
- Emit `IR-012` for undefined module variables.
- Emit `IR-013` for recursive module-variable substitution.

## Verify
- `./venv/bin/pytest tests/unit_tests/lowering tests/unit_tests/netlist -v`
