# T-073 AST->NFIR qualified resolution

## Task summary
- **DoD**: Resolve qualified `ns.symbol` references during AST->NFIR conversion using `NameEnv` and `ProgramDB`. Set instance `ref` + `ref_file_id` and emit `IR-010` for unresolved qualified symbols. Add IR tests for imported resolution and unresolved diagnostics.
- **Verify**: `pytest tests/unit_tests/ir -v`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_import.md`
- `docs/specs/spec_asdl_nfir.md`
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/ir/nfir/dialect.py`
- `src/asdl/imports/name_env.py`
- `src/asdl/imports/program_db.py`
- `tests/unit_tests/ir/test_converter.py`

## Plan
1. Add IR tests for qualified references and unresolved imports.
2. Resolve `ns.symbol` via `NameEnv`/`ProgramDB` and attach `ref_file_id`.
3. Run IR tests and record results.

## Progress log
- 2025-02-14: Added qualified-resolution tests for success and error cases.
- 2025-02-14: Implemented qualified resolution + `ref_file_id` plumbing for instances.
- 2025-02-14: Ran `./venv/bin/pytest tests/unit_tests/ir -v`.

## Patch summary
- Added qualified-symbol resolution coverage in IR converter tests.
- Added optional `ref_file_id` on NFIR instances and resolved `ns.symbol` via imports.

## PR URL
- https://github.com/Jianxun/ASDL/pull/70

## Verification
- `./venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Ready for review.

## Blockers / Questions
- None.

## Next steps
- Await reviewer feedback.
