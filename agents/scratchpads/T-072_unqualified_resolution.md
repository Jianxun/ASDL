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
- [x] Add IR tests for local unqualified resolution and missing-symbol errors.
- [x] Enforce unqualified resolution in AST->NFIR with `IR-011` diagnostics.
- [x] Run `pytest tests/unit_tests/ir -v`.

## Progress log
- Added unqualified resolution checks with `IR-011` diagnostics and a NameEnv helper.
- Added IR tests for local resolution, missing symbols, and import-only unqualified usage.
- Updated the pattern-token test fixture to define the referenced device.
- Verified `pytest tests/unit_tests/ir -v`.

## Patch summary
- `src/asdl/ir/converters/ast_to_nfir.py`: validate unqualified refs against local symbols and emit `IR-011`.
- `src/asdl/imports/name_env.py`: add per-file lookup helper for local symbols.
- `tests/unit_tests/ir/test_converter.py`: add unqualified resolution tests and update fixtures.

## Verification
- `./venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Done.

## Blockers / Questions
- None.

## Next steps
- None.
