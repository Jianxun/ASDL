# T-072 AST->NFIR unqualified resolution

## Task summary
- **DoD**: Resolve unqualified symbols only within the current file during AST->NFIR conversion and emit `IR-011` for unresolved unqualified symbols. Add IR tests for local resolution and missing-symbol diagnostics.
- **Verify**: `pytest tests/unit_tests/ir -v`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_import.md`
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/imports/name_env.py`
- `tests/unit_tests/ir/test_converter.py`

## Plan
1. Wire unqualified resolution using the per-file symbol map only.
2. Emit `IR-011` for missing locals and ensure diagnostics include spans.
3. Add focused IR tests and run the verify command.

## Progress log
- Not started yet.

## Status request
- None.

## Blockers / Questions
- None.

