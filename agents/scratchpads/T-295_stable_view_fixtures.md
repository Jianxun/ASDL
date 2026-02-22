# T-295 - Replace example-based view regressions with stable test fixtures

## Goal
Move view-binding and mixed-view regression coverage to stable fixtures under `tests/`.

## Notes for Executor
- Do not depend on files under `examples/`.
- Include baseline selection, scoped override, and later-rule precedence scenarios.
- Keep fixtures minimal and deterministic.

## Verify
- `./venv/bin/pytest tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view and fixture" -v`
