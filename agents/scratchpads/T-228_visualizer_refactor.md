# T-228: Visualizer Extension Refactor

## Task summary (DoD + verify)
- DoD: Split `extensions/asdl-visualizer/src/extension.ts` into focused modules under
  `extensions/asdl-visualizer/src/extension/` (commands, webview, layout, symbols,
  dump runner, util/types) and keep `extension.ts` as a thin entrypoint. Ensure
  behavior remains unchanged.
- Verify: `npm run build`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `extensions/asdl-visualizer/src/extension.ts`

## Plan
- Capture current behavior and split into focused modules under `src/extension/`.
- Rewire `extension.ts` as a thin entrypoint + command registration.
- Verify build (or record why skipped).

## Todo
- [x] Split `extension.ts` into focused modules (commands, webview, layout, symbols, dump runner, util/types).
- [x] Run `npm run build`.

## Progress log
- 2026-01-26 01:37 — Intake T-228; reviewed task context + extension entrypoint; set task status to in_progress; next step split extension.ts into modules.
- 2026-01-26 01:42 — Split visualizer extension into module files + rewired entrypoint; created new `src/extension/` modules; commit ad2d561; next step run build + update scratchpad.
- 2026-01-26 01:43 — Verified `npm run build` in `extensions/asdl-visualizer`; succeeded with Vite warning about CJS API; next step update scratchpad + prep PR.

## Patch summary
- (pending)

## PR URL
- (pending)

## Verification
- `npm run build`

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Create `extensions/asdl-visualizer/src/extension/` modules and refactor entrypoint.
