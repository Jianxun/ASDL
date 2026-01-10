# T-086 Named pattern macro expansion (<@name>)

## Task summary (DoD + verify)
- Implement module-local named pattern substitution for `<@name>` prior to AST->NFIR conversion (no recursion).
- Reject undefined names and invalid pattern definitions (non-group tokens).
- Add IR tests for substitution and diagnostics.
- Verify: `pytest tests/unit_tests/ir/test_converter.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Inspect AST models and AST->NFIR converter for pattern handling and diagnostics.
- Add tests for named pattern substitution + error cases.
- Implement substitution + validation before AST->NFIR conversion.
- Run IR unit tests and capture results.
 - Todo:
   - [x] Locate pattern handling paths in AST->NFIR and tests.
   - [x] Add converter tests for substitution and diagnostics.
   - [x] Implement named pattern substitution + validation in converter.
   - [x] Run `pytest tests/unit_tests/ir/test_converter.py -v`.

## Progress log
- 2026-01-12: Initialized scratchpad.
- 2026-01-12: Understood task as adding <@name> macro substitution in AST->NFIR with errors for undefined/invalid patterns.
- 2026-01-12: Added IR converter tests and implemented named pattern substitution/validation.
- 2026-01-12: Verified IR converter tests.

## Patch summary
- Added named pattern substitution/validation in AST->NFIR conversion.
- Added converter tests for substitution and diagnostics.

## PR URL
- https://github.com/Jianxun/ASDL/pull/92

## Verification
- `./venv/bin/pytest tests/unit_tests/ir/test_converter.py -v`

## Status request
- Done

## Blockers / Questions
- None yet.

## Next steps
- Locate existing pattern token types and diagnostics hooks.
