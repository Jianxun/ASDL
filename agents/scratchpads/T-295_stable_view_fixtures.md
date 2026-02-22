# T-295 - Build stable view fixture foundation for binding regressions

## Task summary (DoD + verify)
- Add dedicated stable fixtures under `tests/unit_tests/views/fixtures/` that encode:
  - baseline selection
  - scoped override
  - later-rule precedence
- Migrate at least one resolver test and one CLI netlist test to these fixtures so behavior no longer depends on `examples/`.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view and fixture" -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `tests/unit_tests/views/test_view_resolver.py`
- `tests/unit_tests/cli/test_netlist.py`

## Plan
1. Create self-contained view fixture ASDL/config/expected binding files under `tests/unit_tests/views/fixtures/`.
2. Migrate resolver regression coverage for baseline/scoped/later-precedence to use new fixtures.
3. Migrate one CLI netlist view-binding regression to same fixture set.
4. Run task verify command and record results.

## Milestone notes
- Intake complete; task moved to `in_progress` and task-state lint passes.
