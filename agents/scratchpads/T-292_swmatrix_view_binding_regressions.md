# T-292 — Add swmatrix regression coverage for config-driven view binding

## Task summary (DoD + verify)
- DoD:
  Add regression coverage using swmatrix fixture files for global module substitution, scoped path override, and later-rule precedence. Verify sidecar payload fields (`path`, `instance`, `resolved`) and at least one mixed-view netlist emission that contains both default and non-default realization names in output references.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_netlist.py tests/unit_tests/views/test_view_resolver.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Prepare task state + branch.
- Add/adjust swmatrix fixtures for view binding scenarios.
- Add resolver and CLI regression assertions for substitution/overrides/precedence and sidecar fields.
- Verify with targeted tests then task verify command.
- Close out state, PR metadata, and handoff notes.

## Milestone notes
- Intake complete; task moved to `in_progress`.
- Built self-contained `tb_swmatrix_row` fixture design/config/binding files for deterministic regression coverage.
- Added resolver regression tests for module substitution, scoped override, and later-rule precedence using checked-in swmatrix fixtures.
- Added CLI regression test that validates sidecar `path`/`instance`/`resolved` payload and asserts mixed-view emitted call refs include both default and non-default realized names.

## Patch summary
- Fixture updates:
  - `examples/libs/tb/tb_swmatrix/tb_swmatrix_row.asdl`
  - `examples/libs/tb/tb_swmatrix/tb_swmatrix_row.config.yaml`
  - `examples/libs/tb/tb_swmatrix/tb_swmatrix_row.binding.yaml` (new)
- Test coverage updates:
  - `tests/unit_tests/views/test_view_resolver.py`
  - `tests/unit_tests/cli/test_netlist.py`
- Commits:
  - `085a5a4` test(fixtures): add self-contained swmatrix view-binding regression fixtures
  - `9a5b7ce` test(views): cover swmatrix substitution, scope overrides, and precedence

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -v` (pass)
- `./venv/bin/pytest tests/unit_tests/cli/test_netlist.py tests/unit_tests/views/test_view_resolver.py -v` (pass)

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Push branch and open PR.
- Set `T-292` to `ready_for_review` with PR number, keep `merged: false`, and lint task state.
