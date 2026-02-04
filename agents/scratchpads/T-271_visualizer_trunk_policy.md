# T-271 Visualizer single-trunk routing policy

## Task summary (DoD + verify)
- DoD: Update trunk routing to a single hub-aligned trunk through the hub that extends in both directions along the trunk axis and connects each endpoint with one orthogonal branch. Ensure endpoints behind the hub are reachable and no intermediate anchors are introduced. Update dev harness/payload fixtures to cover behind-hub endpoints.
- Verify: `npm --prefix extensions/asdl-visualizer run build:webview`.

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [x] Inspect trunk routing implementation and current dev harness fixtures.
- [x] Implement single-trunk routing through hub with two-way extension and orthogonal branches.
- [x] Update dev harness/payload fixtures for behind-hub endpoints coverage.
- [x] Run verify command.

## Todo
- [x] Adjust trunk routing algorithm to allow behind-hub endpoints and single trunk.
- [x] Update dev harness fixture to include behind-hub endpoints cases.
- [x] Update dev payload JSON to cover behind-hub endpoints.
- [x] Run `build:webview` verify.

## Milestone notes
- Intake: 2026-02-04

## Patch summary
- Updated trunk routing to derive trunk anchors from endpoint projections plus the hub.
- Adjusted dev harness and payload placements to include behind-hub trunk endpoints.

## PR URL
- https://github.com/Jianxun/ASDL/pull/287

## Verification
- `npm --prefix extensions/asdl-visualizer run build:webview`

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
- Await review.
