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
- [ ] Record task status + branch in scratchpad, commit prep updates.
- [ ] Update extension types/symbol parsing for label policy + conn_label.
- [ ] Update gf180mcu symbol sidecar with label policy metadata.
- [ ] Run build verification.
- [ ] Update scratchpad, set ready_for_review, open PR.

## Progress log
- 2026-01-29 21:14 — Task intake; reviewed role + task context; updated scratchpad/task state; created feature branch; next step update extension types.

## Patch summary

## PR URL

## Verification

## Status request

## Blockers / Questions

## Next steps
