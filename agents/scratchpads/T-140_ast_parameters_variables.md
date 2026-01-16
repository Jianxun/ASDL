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
- `tests/unit_tests/ir/fixtures/graphir_single_file.asdl`
- `tests/unit_tests/cli/test_netlist.py`
- `tests/unit_tests/e2e/test_pipeline_mvp.py`

## Plan
- Inspect AST models/parser for `params` and introduce `parameters` + `variables`.
- Update fixtures/tests to use `parameters` and add `variables` parsing coverage.
- Run AST unit tests per verify command.

## Todo
- [ ] Update AST models/parser for `parameters` + `variables`.
- [ ] Refresh AST-facing fixtures/tests and add `variables` coverage.
- [ ] Run verification.

## Progress log
- 2026-01-18: Created scratchpad and prepared task.

## Patch summary
- TBD.

## PR URL
- TBD.

## Verification
- TBD.

## Status request
- In Progress.

## Blockers / Questions
- None.

## Next steps
- Implement AST model/parser changes and update tests.
