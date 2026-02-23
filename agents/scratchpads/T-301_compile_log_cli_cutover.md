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

## Patch summary
- Pending.

## PR URL
- Pending.

## Verification
- Pending.

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Implement code + tests, run verify, open PR, set `ready_for_review`.
