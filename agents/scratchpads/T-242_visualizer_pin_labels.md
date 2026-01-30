# T-242: Render numeric pin labels + forced labels in webview

## Task summary (DoD + verify)
- Render connection labels at pin handles for numeric patterns using `<3>` and tuple
  `<3,1>` formatting with `;` joins.
- Honor pin `label: always` by rendering net/slice labels when no numeric label exists.
- Labels respect symbol orientation and stay inside the body edge.
- Verify: `cd extensions/asdl-visualizer && npm run build`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Inspect webview rendering for pin labels and orientation handling.
- Implement numeric/forced label rendering and adjust styles to keep labels inside body.
- Update dev harness if needed to exercise label cases.
- Run webview build verify.

## Progress log
- 2026-01-29 21:27 — Task intake; reviewed role and project context; ready to set status in progress and branch; next step update task state and create branch.
- 2026-01-29 21:34 — Set T-242 status to in_progress and created `feature/T-242-pin-labels`; linted task state; next step update webview rendering for pin labels.

## Patch summary

## PR URL

## Verification

## Status request

## Blockers / Questions

## Next steps
