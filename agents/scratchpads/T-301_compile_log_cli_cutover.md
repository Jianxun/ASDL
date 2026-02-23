# T-301 — Implement consolidated compile log JSON and CLI `--log` hard cutover

## Task summary (DoD + verify)
- DoD:
  Add CLI `--log <path>` and default compile-log output path
  `<entry_file_basename>.log.json`; remove legacy `--binding-sidecar` flow in a
  hard cutover. Emit deterministic compile log JSON with at least
  `view_bindings`, `emission_name_map`, and warning/diagnostic metadata, and
  surface write failures as CLI diagnostics.
- Verify:
  `./venv/bin/pytest tests/unit_tests/cli/test_netlist.py tests/unit_tests/views/test_view_resolver.py -k "log or view_bindings or emission_name_map or sidecar" -v`

## Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Inspect existing CLI sidecar/log behavior and current test coverage.
- Implement `--log` hard cutover and deterministic compile log payload plumbing.
- Add/update regressions for CLI + resolver behavior and failure diagnostics.
- Run targeted verify command and record results.

## Milestone notes
- Intake complete; task set to `in_progress`.
- Implemented CLI hard cutover from `--binding-sidecar` to `--log`.
- Added consolidated compile-log payload generation and default log path behavior.
- Updated CLI regressions to assert compile-log sections and removed sidecar flag usage.

## Patch summary
- Updated `asdlc netlist` option surface in `src/asdl/cli/__init__.py`:
  - removed `--binding-sidecar`
  - added `--log <path>`
  - defaulted compile log path to `<entry_file_basename>.log.json`
  - generated deterministic compile-log JSON containing:
    - `view_bindings`
    - `emission_name_map`
    - warnings/diagnostics metadata (`warning_count`, `warnings`, `diagnostic_count`,
      `diagnostic_severity_counts`, `diagnostics`)
  - added CLI diagnostics for compile-log write failures (`TOOL-002` path)
- Updated netlist CLI tests in `tests/unit_tests/cli/test_netlist.py`:
  - migrated sidecar tests to compile-log assertions
  - added coverage for default compile-log path output
  - added regression that `--binding-sidecar` is rejected
  - added coverage for compile-log write-failure diagnostics

## PR URL
- Pending PR creation.

## Verification
- `./venv/bin/pytest tests/unit_tests/cli/test_netlist.py tests/unit_tests/views/test_view_resolver.py -k "log or view_bindings or emission_name_map or sidecar" -v`
  - Result: 14 passed, 18 deselected

## Status request (Done / Blocked / In Progress)
- Done

## Blockers / Questions
- None.

## Next steps
- Push branch, open PR to `main`, set task state to `ready_for_review`.
