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

## Patch summary
- (pending)

## PR URL
- (pending)

## Verification
- (pending)

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Review `src/asdl/core/dump.py` and pattern utilities to locate expansion rules for visualizer dump.
