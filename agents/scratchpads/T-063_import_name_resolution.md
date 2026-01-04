# T-063 Import Name Resolution

## Task summary
- DoD: Wire import-aware name resolution into AST->NFIR conversion: allow unqualified symbols only from the current file, and `ns.symbol` for imported files; reject unresolved names with diagnostics. Forbid same-name symbol duplicates within a file regardless of kind. Emit a warning for unused `imports` namespaces. Add IR tests covering local refs, imported refs, unused-import warnings, and unresolved symbol diagnostics.
- Verify: `pytest tests/unit_tests/ir -v`

## Read
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/ir/nfir/dialect.py`
- `src/asdl/imports/program_db.py`
- `src/asdl/imports/name_env.py`
- `src/asdl/imports/diagnostics.py`
- `tests/unit_tests/ir/`

## Plan
- Update AST->NFIR conversion entrypoint to accept import resolution context.
- Resolve unqualified names to current file only; `ns.symbol` via `NameEnv`.
- Emit errors for missing symbols and duplicates within the same file.
- Track referenced namespaces to emit unused-import warnings.
- Add unit tests for the new resolution and warnings.

## Progress log
- Initialized scratchpad.

## Patch summary
- TBD.

## Verification
- TBD.

## Blockers / Questions
- None.

## Next steps
- Implement name resolution wiring and add tests.
