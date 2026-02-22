# T-296 - Remove remaining example-based view regressions

## Goal
Eliminate remaining view-binding regression dependencies on `examples/` and rely only on stable fixtures under `tests/`.

## Notes for Executor
- Keep scenario coverage: global substitution, scoped override, and later-rule precedence.
- Ensure CLI and resolver tests no longer read fixture inputs from `examples/`.

## Verify
- `./venv/bin/pytest tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view and fixture" -v`
