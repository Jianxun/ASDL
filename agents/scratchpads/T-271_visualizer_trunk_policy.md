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
- [ ] Inspect trunk routing implementation and current dev harness fixtures.
- [ ] Implement single-trunk routing through hub with two-way extension and orthogonal branches.
- [ ] Update dev harness/payload fixtures for behind-hub endpoints coverage.
- [ ] Run verify command.

## Todo
- [ ] Adjust trunk routing algorithm to allow behind-hub endpoints and single trunk.
- [ ] Update dev harness fixture to include behind-hub endpoints cases.
- [ ] Update dev payload JSON to cover behind-hub endpoints.
- [ ] Run `build:webview` verify.

## Milestone notes
- Intake: 2026-02-04

## Patch summary
- 

## PR URL
- 

## Verification
- 

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- 
