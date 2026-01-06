# T-073 AST->NFIR qualified resolution

## Task summary
- **DoD**: Resolve qualified `ns.symbol` references during AST->NFIR conversion using `NameEnv` and `ProgramDB`. Set instance `ref` + `ref_file_id` and emit `IR-010` for unresolved qualified symbols. Add IR tests for imported resolution and unresolved diagnostics.
- **Verify**: `pytest tests/unit_tests/ir -v`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_import.md`
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/imports/name_env.py`
- `src/asdl/imports/program_db.py`
- `tests/unit_tests/ir/test_converter.py`

## Plan
1. Resolve `ns.symbol` by mapping `ns` to `file_id`, then lookup in ProgramDB.
2. Populate `ref`/`ref_file_id` and emit `IR-010` when resolution fails.
3. Add IR tests for qualified references and unresolved imports.

## Progress log
- Not started yet.

## Status request
- None.

## Blockers / Questions
- None.

