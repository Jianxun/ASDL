# Task summary (DoD + verify)
- DoD: Keep `schema_version: 0` but replace `pin_offsets` with inline pin metadata entries in `design.sym.yaml`. Accept pin list entries as `string | null | {pin: {offset?, visible?}}`, validate single-key maps, and default `visible` to true. Remove legacy parsing, emit diagnostics for malformed pin entries, and update pin placement to use per-pin offsets. Extend `glyph` metadata to include explicit placement `glyph.box: {x,y,w,h}` in grid units so glyph scaling is specified by schema instead of inferred. Update the visualizer spec and add a gf180mcu symbol sidecar that uses the new format.
- Verify: `cd extensions/asdl-visualizer && npm run build`

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs/spec_asdl_visualizer.md
- extensions/asdl-visualizer/src/extension/types.ts
- extensions/asdl-visualizer/src/extension/symbols.ts
- extensions/asdl-visualizer/src/webview/app.tsx
- examples/pdks/gf180mcu/asdl/gf180mcu.asdl

# Plan
- Update symbol schema types/parsing to inline pin metadata + glyph box.
- Update webview pin placement to consume inline offsets and keep metadata.
- Add gf180mcu symbol sidecar in new schema and adjust spec text if needed.
- Verify build for the visualizer extension.

# Progress log
- 2026-01-27 02:28 — Task intake; reviewed executor workflow, task card, and symbol schema code; next step update types/parsers and webview pin placement.
- 2026-01-27 02:30 — Updated visualizer symbol schema types/parsing for inline pin metadata and glyph boxes; adjusted webview pin placement to use per-pin offsets; files touched: extensions/asdl-visualizer/src/extension/types.ts, extensions/asdl-visualizer/src/extension/symbols.ts, extensions/asdl-visualizer/src/webview/app.tsx.
- 2026-01-27 02:31 — Committed schema parsing + webview pin placement updates (d1dff70).
- 2026-01-27 02:32 — Added gf180mcu symbol sidecar + spec note for single-key pin metadata maps (35fc93f).
- 2026-01-27 02:31 — Fixed mock symbol pins to use new pin metadata shape after build error; file touched: extensions/asdl-visualizer/src/extension/symbols.ts.
- 2026-01-27 02:32 — Committed mock symbol pin fix (4775c4f).
- 2026-01-27 02:33 — Verified visualizer build (cd extensions/asdl-visualizer && npm run build).

# Patch summary
- Updated symbol schema parsing/types to inline pin metadata and validate glyph boxes; removed pin_offsets usage.
- Adjusted webview pin placement to read per-pin offsets/visibility metadata.
- Added gf180mcu symbol sidecar and clarified spec single-key pin metadata rule.

# PR URL
- https://github.com/Jianxun/ASDL/pull/248

# Verification
- `cd extensions/asdl-visualizer && npm run build`
  - Result: success (warns about Vite CJS deprecation).

# Status request (Done / Blocked / In Progress)
- Ready for Review

# Blockers / Questions
- None.

# Next steps
- Await review.
- 2026-01-27 02:33 — Opened PR https://github.com/Jianxun/ASDL/pull/248.
- 2026-01-27 02:33 — Set task status to ready_for_review in agents/context/tasks_state.yaml.
