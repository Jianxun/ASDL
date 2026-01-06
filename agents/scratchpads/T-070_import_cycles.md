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
- Not started yet.

## Status request
- None.

## Blockers / Questions
- None.

