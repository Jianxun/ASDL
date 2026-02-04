# T-270 Visualizer dynamic routing recompute

## Task summary (DoD + verify)
- DoD: Update the visualizer webview so topology routing recomputes whenever node positions change (drag/move), including MST. Ensure the updated edge graph preserves pin label behavior and connect_by_label suppression. Update dev harness/payload fixtures to exercise dynamic recompute.
- Verify: `npm --prefix extensions/asdl-visualizer run build:webview`.

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [ ] Inspect visualizer state management and routing flow post-refactor.
- [ ] Implement routing recompute on node position changes (including MST) while preserving pin labels/connect_by_label suppression.
- [ ] Update dev harness/payload fixtures for dynamic recompute coverage.
- [ ] Run verify command.

## Todo
- [ ] Add routing recompute helpers based on live node positions.
- [ ] Wire node-change handler to rebuild routing + junction nodes.
- [ ] Update dev harness/payload fixtures for connect_by_label + recompute coverage.
- [ ] Run `build:webview` verify.

## Milestone notes
- Intake: 2026-02-04

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Implement dynamic recompute and update fixtures.
