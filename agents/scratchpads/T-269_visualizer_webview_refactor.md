# T-269 Visualizer webview refactor

## Task summary (DoD + verify)
- DoD: Split `extensions/asdl-visualizer/src/webview/app.tsx` into smaller modules without changing runtime behavior. Extract: (1) routing algorithms (star/mst/trunk), (2) layout/geometry helpers (orient transforms, pin placement, grid conversions), (3) node components (instance/hub/junction), (4) message handling + state hooks, and (5) shared constants/types. Keep ReactFlow wiring intact and update imports/exports accordingly.
- Verify: `npm --prefix extensions/asdl-visualizer run build:webview`.

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [ ] Inspect `app.tsx` and related visualizer modules.
- [ ] Identify cohesive slices for routing, layout/geometry, nodes, state/messages, and shared types.
- [ ] Extract modules with consistent exports/imports; keep behavior unchanged.
- [ ] Update tests/build as needed; run verify command.

## Todo
- [x] Add shared types/constants modules.
- [x] Move geometry/layout/routing helpers.
- [x] Extract node components.
- [x] Add state/message hook and rewire `app.tsx`.
- [x] Run `build:webview` verify.

## Milestone notes
- Intake: 2026-02-04

## Patch summary
- Added shared webview constants/types modules.
- Split geometry, layout, and routing helpers into dedicated graph modules.
- Extracted instance/hub/junction node components.
- Added `useVisualizerState` hook for message handling/state and rewired `app.tsx`.

## PR URL
- TBD

## Verification
- `npm --prefix extensions/asdl-visualizer run build:webview`

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Prep PR and update task state.
