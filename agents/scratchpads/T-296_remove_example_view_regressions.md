# T-296 — Remove remaining example-based view regressions

## Task summary (DoD + verify)
- Remove remaining regression-test dependencies on `examples/` for view binding and mixed-view emission coverage.
- Update resolver and CLI tests to consume only stable fixtures under `tests/`.
- Preserve scenario coverage: global substitution, scoped override, and later-rule precedence.
- Fixture suite must remain self-contained and support hypothetical stress cases independent of project example libraries.

Verify:
- `./venv/bin/pytest tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view and fixture" -v`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `tests/unit_tests/views/test_view_resolver.py`
- `tests/unit_tests/cli/test_netlist.py`
- `tests/unit_tests/views/fixtures/view_binding_fixture.asdl`
- `tests/unit_tests/views/fixtures/view_binding_fixture.config.yaml`
- `tests/unit_tests/views/fixtures/view_binding_fixture.config_3.binding.yaml`

## Plan
1. Audit resolver/CLI view regression tests for non-fixture and example-coupled inputs.
2. Migrate remaining CLI view regression checks to stable fixture inputs under `tests/unit_tests/views/fixtures`.
3. Keep coverage for baseline/global substitution, scoped override, and later-rule precedence.
4. Verify with the task command and record results.

## Milestone notes
- Intake complete; task state moved to `in_progress` and task-state linter passed.
- Migrated CLI view-regression tests to fixture-driven inputs and output paths under `tmp_path` to prevent fixture-directory artifacts.

## Patch summary
- Updated `tests/unit_tests/cli/test_netlist.py` view regression tests to use `VIEW_FIXTURE_ASDL` + `VIEW_FIXTURE_CONFIG` instead of ad-hoc inline YAML profiles for fixture scenarios.
- Added fixture-driven CLI coverage for scoped override output refs (`config_2`) and fixture-profile emission differences (`config_1` vs `config_2`).
- Ensured sidecar regression test remains deterministic on fixture content and that generated netlist outputs stay in temporary test paths.
- Removed now-unused inline view helper builders that were superseded by fixture-based coverage.

## PR URL
- Pending PR creation.

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view and fixture" -v`
  - Result: 7 passed, 19 deselected

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Push branch and open PR against `main`.
- Update `agents/context/tasks_state.yaml` to `ready_for_review` with PR number, set `merged: false`, and lint state file.
