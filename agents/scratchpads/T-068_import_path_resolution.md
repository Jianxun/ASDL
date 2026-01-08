# T-068 Import path resolution core

## Task summary
- **DoD**: Implement import path resolution per `docs/specs/spec_asdl_import.md` (env expansion, relative/absolute handling, ordered logical roots, normalization, `AST-010` missing-path errors, `AST-011` malformed paths). Add tests for resolution order, env expansion, relative/absolute handling, and missing paths.
- **Verify**: `pytest tests/unit_tests/parser -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_import.md`
- `src/asdl/imports/resolver.py`
- `src/asdl/imports/diagnostics.py`
- `tests/unit_tests/parser/test_import_resolution.py`

## Plan
1. Add import resolution tests for relative/absolute, env expansion, root order, missing paths.
2. Implement diagnostics + resolver helpers to satisfy the spec behavior.
3. Run parser test suite.

## Todo
- [x] Add tests for import resolution path handling + root ordering.
- [x] Implement resolver/diagnostics core for import paths.
- [x] Run parser unit tests.

## Progress log
- Added import resolution tests for relative/absolute/env/logical path cases + missing path.
- Implemented import diagnostics helpers and core path resolver with env expansion,
  ordered roots, and normalization.
- Ran `pytest tests/unit_tests/parser/test_import_resolution.py -v`.
- Ran `pytest tests/unit_tests/parser -v`.

## Patch summary
- Added import resolution tests at `tests/unit_tests/parser/test_import_resolution.py`.
- Implemented import path diagnostics in `src/asdl/imports/diagnostics.py`.
- Implemented path resolution logic in `src/asdl/imports/resolver.py`.

## PR URL
- https://github.com/Jianxun/ASDL/pull/62

## Verification
- `./venv/bin/pytest tests/unit_tests/parser/test_import_resolution.py -v`
- `./venv/bin/pytest tests/unit_tests/parser -v`

## Status request
- Ready for review.

## Blockers / Questions
- None.
