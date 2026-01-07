# T-074 Unused import lint

## Task summary
- **DoD**: Emit `LINT-001` warnings for unused import namespaces during AST->NFIR conversion. Add IR tests covering unused and used import namespaces.
- **Verify**: `pytest tests/unit_tests/ir -v`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_import.md`
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/imports/name_env.py`
- `tests/unit_tests/ir/test_converter.py`

## Plan
1. Track namespace usage during conversion and compare against declared imports.
2. Emit `LINT-001` warnings with spans for unused namespaces.
3. Add IR tests for used/unused cases and run the verify command.

## Progress log
- Added IR tests for used/unused import namespaces.
- Implemented LINT-001 warnings for unused namespaces during AST->NFIR conversion.
- Adjusted error-path test expectations to allow lint warnings.
- Verified `pytest tests/unit_tests/ir -v`.

## Patch summary
- `src/asdl/ir/converters/ast_to_nfir.py`: track qualified namespace usage and emit LINT-001 warnings.
- `tests/unit_tests/ir/test_converter.py`: add used/unused namespace coverage and accept lint warnings on error cases.

## Verification
- `./venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Ready for review.

## Next steps
- Open PR and hand off to Reviewer.

## Blockers / Questions
- None.
