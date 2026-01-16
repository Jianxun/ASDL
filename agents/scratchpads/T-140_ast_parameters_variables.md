# T-140 AST parameters rename and variables blocks

## Task summary (DoD + verify)
- Rename device/backend AST fields from `params` to `parameters` and add
  `variables` blocks for modules, devices, and device backends. Update AST
  models and parsing to accept only `parameters` (reject `params`). Refresh
  existing AST-facing fixtures/tests to use `parameters`, and add coverage
  for parsing `variables` blocks.
- Verify:
  - `venv/bin/pytest tests/unit_tests/ast -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `src/asdl/ir/converters/ast_to_graphir_lowering.py`
- `tests/unit_tests/ast/test_models.py`
- `docs/specs/spec_ast.md`
- `tests/unit_tests/ir/fixtures/graphir_single_file.asdl`
- `tests/unit_tests/cli/test_netlist.py`
- `tests/unit_tests/e2e/test_pipeline_mvp.py`

## Plan
- Inspect AST models/parser for `params` and introduce `parameters` + `variables`.
- Update fixtures/tests to use `parameters` and add `variables` parsing coverage.
- Run AST unit tests per verify command.

## Todo
- [x] Update AST models/parser for `parameters` + `variables`.
- [x] Refresh AST-facing fixtures/tests and add `variables` coverage.
- [x] Run verification.

## Progress log
- 2026-01-18: Created scratchpad, set task status, and branched.
- 2026-01-18: Updated AST models/lowering, fixtures, and tests for parameters/variables.
- 2026-01-18: Ran AST unit tests.

## Patch summary
- Added AST `parameters`/`variables` fields with backend `params` rejection.
- Updated AST fixtures and CLI/e2e YAML to use `parameters`.
- Added AST test coverage for `variables` parsing and `params` rejection.

## PR URL
- https://github.com/Jianxun/ASDL/pull/148

## Verification
- `venv/bin/pytest tests/unit_tests/ast -v`

## Status request
- Done.

## Blockers / Questions
- None.

## Next steps
- Await review.
