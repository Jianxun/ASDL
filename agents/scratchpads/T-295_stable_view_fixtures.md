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

## Patch summary
- Added stable, self-contained fixture assets:
  - `tests/unit_tests/views/fixtures/view_binding_fixture.asdl`
  - `tests/unit_tests/views/fixtures/view_binding_fixture.config.yaml`
  - `tests/unit_tests/views/fixtures/view_binding_fixture.config_3.binding.yaml`
- Migrated resolver regression tests to fixture-backed scenarios for:
  - baseline selection (`config_1`)
  - scoped override (`config_2`)
  - later-rule precedence (`config_3`)
- Migrated one CLI netlist regression to the same fixture set and kept mixed-view emission assertions.

## PR URL
- Pending creation in closeout.

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view and fixture" -v`
  - Result: pass (4 passed, 21 deselected)

## Status request
- Ready for review after PR is opened and task state is updated with PR number.

## Blockers / Questions
- None.

## Next steps
- Push `feature/T-295-stable-view-fixtures`.
- Open PR to `main`.
- Update `agents/context/tasks_state.yaml` to `ready_for_review` with PR number and lint.
