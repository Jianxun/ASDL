# T-286 Structured Instance Regression Coverage

## Task summary (DoD + verify)
- DoD: Add explicit regression tests that fail if structured instance forms crash or diverge from inline semantics in end-to-end netlist generation. Cover one positive case and one malformed case that reports diagnostics rather than raising exceptions.
- Verify: `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/cli/test_netlist.py -v`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `tests/unit_tests/core/test_patterned_graph_lowering.py`
- `tests/unit_tests/cli/test_netlist.py`
- `src/asdl/lowering/ast_to_patterned_graph_instances.py`
- `src/asdl/ast/instance_expr.py`
- `src/asdl/cli/__init__.py`

## Plan
1. Add core regression tests for structured-instance semantic parity and malformed structured payload diagnostics.
2. Add CLI regression tests for structured-instance netlist parity and malformed structured parse diagnostics.
3. Run task verify command and commit focused test-only changes.
4. Push branch, open PR to `main`, and set task state to `ready_for_review`.

## Milestone notes
- Confirmed `T-286` state was `ready`; set to `in_progress` and linted task state.
- Added focused regressions without touching implementation code.
- Verified both target test suites pass with new coverage.

## Patch summary
- `tests/unit_tests/core/test_patterned_graph_lowering.py`
  - Added structured vs inline lowering parity regression.
  - Added malformed structured payload regression asserting `IR-001` diagnostic (no exception).
- `tests/unit_tests/cli/test_netlist.py`
  - Added structured-instance pipeline fixture and parity regression ensuring generated netlist matches inline form.
  - Added malformed structured-instance fixture using `params` alias and regression asserting `PARSE-003` diagnostic.

## PR URL
- Pending creation in closeout step.

## Verification
- `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/cli/test_netlist.py -v`
  - Result: PASS (`33 passed`)

## Status request
- In Progress (ready to open PR and move task to `ready_for_review`)

## Blockers / Questions
- None.

## Next steps
1. Push feature branch.
2. Open PR against `main`.
3. Update `agents/context/tasks_state.yaml` with `ready_for_review` and PR number, then lint.
