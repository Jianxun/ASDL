# T-139 Module-local named pattern macro expansion

## Task summary (DoD + verify)
- Implement module-local named pattern substitution for `<@name>` as an AST
  elaboration step before AST->GraphIR lowering.
- Replace `<@name>` tokens in instance names, net names, endpoint expressions,
  instance params, and instance_defaults bindings with the referenced single-group
  pattern token.
- Enforce pattern name regex, forbid recursion, and emit diagnostics for undefined
  or invalid named patterns.
- Preserve source spans for diagnostics and add unit tests covering successful
  substitution and error cases.
- Verify:
  - `venv/bin/pytest tests/unit_tests/parser -v`
  - `venv/bin/pytest tests/unit_tests/ir -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `src/asdl/ir/converters/ast_to_graphir.py`
- `src/asdl/ir/converters/ast_to_graphir_lowering.py`
- `tests/unit_tests/parser/test_pattern_expansion.py`

## Plan
- Add tests for named pattern substitution success and diagnostics.
- Extend AST location tracking for named pattern references.
- Implement named pattern elaboration step before AST->GraphIR lowering.
- Update converter wiring and diagnostics; ensure spans are preserved.
- Run verify commands.

## Todo
- [x] Add named pattern elaboration tests.
- [x] Implement AST location tracking and elaboration helper.
- [x] Wire converter and update exports.
- [x] Run verification.

## Progress log
- 2026-01-18: Set task status to in_progress, created feature branch.
- 2026-01-18: Added named pattern elaboration, location tracking, and tests.

## Patch summary
- Added named pattern elaboration helpers, diagnostics, and AST location tracking.
- Wired elaboration into AST->GraphIR conversion.
- Added parser + IR unit tests for named pattern macro substitution.

## PR URL
- Pending.

## Verification
- `venv/bin/pytest tests/unit_tests/parser -v`
- `venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- In Progress.

## Blockers / Questions
- None.

## Next steps
- Implement tests and named pattern elaboration.
