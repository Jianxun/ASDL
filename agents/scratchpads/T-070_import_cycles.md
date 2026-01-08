# T-070 Import cycle diagnostics

## Task summary
- **DoD**: Detect import cycles, emit `AST-012` with a readable import chain, and add tests for single-cycle and multi-hop cycle reporting.
- **Verify**: `pytest tests/unit_tests/parser -v`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_import.md`
- `src/asdl/imports/resolver.py`
- `src/asdl/imports/diagnostics.py`
- `tests/unit_tests/parser/test_import_resolution.py`

## Plan
1. Add cycle detection to the resolver with explicit stack tracking for chains.
2. Emit `AST-012` with a stable, readable chain format.
3. Add tests for simple and multi-hop cycles and run the verify command.

## Progress log
- Added import cycle tests for single and multi-hop chains.
- Implemented import graph resolution with cycle detection and `AST-012` diagnostics.
- Ran `pytest tests/unit_tests/parser/test_import_resolution.py -v`.

## Patch summary
- Added import-cycle tests to `tests/unit_tests/parser/test_import_resolution.py`.
- Added `AST-012` diagnostics helper in `src/asdl/imports/diagnostics.py`.
- Added import graph resolver with cycle detection in `src/asdl/imports/resolver.py`.

## PR URL
- https://github.com/Jianxun/ASDL/pull/64

## Verification
- `./venv/bin/pytest tests/unit_tests/parser/test_import_resolution.py -v`
- `./venv/bin/pytest tests/unit_tests/parser -v`

## Status request
- Ready for review.

## Blockers / Questions
- None.

## Next steps
- None.
