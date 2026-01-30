# T-241: Consume endpoint labels + pin label policy in extension graph

## Task summary (DoD + verify)
- Extend visualizer dump types and symbol parsing to include pin label policy (`label: auto|always|never`).
- Build GraphPayload edges with optional `conn_label` and emit per-pin label data for the webview.
- Prefer numeric `conn_label` over pin `label: always`.
- Verify: `cd extensions/asdl-visualizer && npm run build`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Inspect extension types/symbol parsing and current symbol schema.
- Update types to include pin label policy + conn_label.
- Update symbol parsing + example symbol YAML.
- Verify build, update scratchpad, and prep PR.

## Todo
- [x] Record task status + branch in scratchpad, commit prep updates.
- [x] Update extension types/symbol parsing for label policy + conn_label.
- [x] Update gf180mcu symbol sidecar with label policy metadata.
- [x] Run build verification.
- [x] Update scratchpad, set ready_for_review, open PR.

## Progress log
- 2026-01-29 21:14 — Task intake; reviewed role + task context; updated scratchpad/task state; created feature branch; next step update extension types.
- 2026-01-29 21:15 — Commit e457701 (chore: start T-241); recorded task state + scratchpad baseline; next step update extension types.
- 2026-01-29 21:17 — Updated visualizer extension types + symbol parsing to capture pin label policy and endpoint conn_label; next step update gf180mcu symbol sidecar.
- 2026-01-29 21:17 — Commit f009041 (feat: add pin label policy to visualizer graph); captured conn_label + pin label parsing; next step update gf180mcu symbol sidecar.
- 2026-01-29 21:18 — Updated gf180mcu symbol sidecar to include pin label policy metadata; next step run build verification.
- 2026-01-29 21:18 — Commit 5589539 (chore: add pin label policy to gf180mcu symbols); refreshed example sidecar; next step run build verification.
- 2026-01-29 21:20 — Ran `npm run build` in `extensions/asdl-visualizer`; build succeeded (vite CJS warning); next step finalize scratchpad + PR.
- 2026-01-29 21:22 — Opened PR https://github.com/Jianxun/ASDL/pull/253; next step update task status + scratchpad.
- 2026-01-29 21:24 — Set T-241 status to ready_for_review with PR 253 and ran tasks_state linter; next step commit scratchpad/state updates.
- 2026-01-29 21:25 — Commit 9d4b9b2 (chore: finalize T-241 status); captured ready_for_review state + scratchpad updates; next step push branch.

## Patch summary
- Added pin label policy + conn_label support to visualizer extension types/graph builder.
- Normalized symbol pin label metadata with defaults and diagnostics.
- Updated gf180mcu symbol sidecar to exercise pin label policy.

## PR URL
https://github.com/Jianxun/ASDL/pull/253

## Verification
 - `cd extensions/asdl-visualizer && npm run build`

## Status request
Ready for review

## Blockers / Questions

## Next steps
- Await review feedback.
