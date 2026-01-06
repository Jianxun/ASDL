# T-071 ProgramDB + NameEnv

## Task summary
- **DoD**: Build `ProgramDB` keyed by `file_id` and a per-file `NameEnv` mapping namespaces to `file_id`s. Deduplicate loads by `file_id`, allow multiple namespaces to bind the same file, and detect duplicate symbol names within a file (`AST-014`). Add tests for deduping and duplicate symbols.
- **Verify**: `pytest tests/unit_tests/parser -v`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_import.md`
- `src/asdl/imports/program_db.py`
- `src/asdl/imports/name_env.py`
- `src/asdl/imports/resolver.py`
- `src/asdl/imports/diagnostics.py`
- `tests/unit_tests/parser/test_import_resolution.py`

## Plan
1. Implement ProgramDB insertion + dedupe rules keyed by normalized `file_id`.
2. Build NameEnv bindings and enforce duplicate symbol checks per file.
3. Add tests covering dedupe and duplicate symbol diagnostics.

## Progress log
- Not started yet.

## Status request
- None.

## Blockers / Questions
- None.

