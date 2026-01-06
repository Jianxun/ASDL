# T-068 Import path resolution core

## Task summary
- **DoD**: Implement import path resolution per `docs/specs/spec_asdl_import.md` (env expansion, relative/absolute handling, ordered logical roots, normalization, `AST-010` missing-path errors, `AST-011` malformed paths). Add tests for resolution order, env expansion, relative/absolute handling, and missing paths.
- **Verify**: `pytest tests/unit_tests/parser -v`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_import.md`
- `src/asdl/imports/resolver.py`
- `src/asdl/imports/diagnostics.py`
- `tests/unit_tests/parser/test_import_resolution.py`

## Plan
1. Implement the core resolution helper(s) with env expansion and normalized `file_id`s.
2. Wire diagnostics for missing/malformed paths and ensure resolution ordering matches spec.
3. Add parser-level tests covering each path category and run the verify command.

## Progress log
- Not started yet.

## Status request
- None.

## Blockers / Questions
- None.

