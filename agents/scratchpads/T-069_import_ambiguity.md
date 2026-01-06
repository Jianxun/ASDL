# T-069 Import ambiguity diagnostics

## Task summary
- **DoD**: Detect ambiguous logical-path matches across roots, emit `AST-015` with ordered match list, and fail resolution. Add tests that assert ordering in the ambiguity diagnostic.
- **Verify**: `pytest tests/unit_tests/parser -v`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_import.md`
- `src/asdl/imports/resolver.py`
- `src/asdl/imports/diagnostics.py`
- `tests/unit_tests/parser/test_import_resolution.py`

## Plan
1. Extend resolution to collect all logical-root matches before choosing.
2. Emit `AST-015` with ordered matches and ensure failure on ambiguity.
3. Add tests for multiple matches and verify diagnostic ordering.

## Todo
- [x] Add ambiguity diagnostic + resolver handling.
- [x] Add ambiguity ordering coverage in parser import resolution tests.

## Progress log
- Updated import resolution tests to avoid multiple-root shadowing and assert ambiguity ordering.
- Added `AST-015` diagnostic helper and resolver logic for multiple logical matches.

## Status request
- None.

## Blockers / Questions
- None.
