# T-240: Expand literal patterns in visualizer dump + add numeric labels

## Task summary (DoD + verify)
- Expand literal enum patterns in instance names and endpoint pin names for visualizer dump.
- Keep numeric range patterns compact; attach per-endpoint numeric labels formatted as `<3>` or `<3,1>`; join multiple slices with `;` per `docs/specs/spec_asdl_pattern_expansion.md`.
- Ensure ota_nmos visualizer dump emits endpoints for `mn_tail.<s|b>` and `mn_in_<n>.d`.
- Verify: `./venv/bin/asdlc visualizer-dump examples/libs/mosbius_devices/ota_nmos/ota_nmos.asdl`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Inspect current visualizer dump generation and pattern handling.
- Add/adjust pattern expansion utilities to expand literal enums while keeping numeric ranges compact with labels.
- Update dump emission to use the new expansion/labeling rules.
- Add/adjust tests if present; otherwise validate with the provided verify command.

## Progress log
- 2026-01-29 20:36 — Read task/contract/context; set T-240 status to in_progress and created feature branch `feature/T-240-visualizer-literal-expand`; next step inspect dump implementation.
- 2026-01-29 20:44 — Commit 780aea4: record T-240 start state (tasks_state + scratchpad); next step add regression coverage for visualizer expansion.
- 2026-01-29 20:47 — Commit 84840e6: added CLI test covering literal enum expansion + numeric label formatting; next step implement visualizer dump expansion helpers.
- 2026-01-29 20:51 — Commit 23a45f5: added visualizer enum expansion + numeric label helpers and wired dump expansion; next step run visualizer-dump verify command.
- 2026-01-29 20:53 — Ran `./venv/bin/asdlc visualizer-dump examples/libs/mosbius_devices/ota_nmos/ota_nmos.asdl` (ok); next step finalize closeout and PR.
- 2026-01-29 20:54 — Opened PR https://github.com/Jianxun/ASDL/pull/252; next step set task status ready_for_review.

## Patch summary
- Added visualizer enum expansion + numeric label helpers in `src/asdl/patterns_refactor/expand.py` and exported via `src/asdl/patterns_refactor/__init__.py`.
- Updated visualizer dump to expand instances/endpoints, emit numeric `conn_label`, and sync net endpoint IDs in `src/asdl/core/dump.py`.
- Added CLI test covering literal enum expansion and numeric labels in `tests/unit_tests/cli/test_visualizer_dump.py`.

## PR URL
- https://github.com/Jianxun/ASDL/pull/252

## Verification
- `./venv/bin/asdlc visualizer-dump examples/libs/mosbius_devices/ota_nmos/ota_nmos.asdl`

## Status request
- Done

## Blockers / Questions
- None.

## Next steps
- Set T-240 status to ready_for_review and await reviewer feedback.
