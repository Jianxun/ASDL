# Task summary (DoD + verify)
- DoD: Resolve `glyph.src` relative to the source `.asdl` file and pass a webview-safe URI to the webview payload. Render the SVG glyph inside instance nodes using the schema-provided `glyph.box` (grid units) and preserve aspect ratio; do not infer scale or coordinates. Honor optional `viewbox` metadata. Emit a diagnostic when glyph resolution fails.
- Verify: cd extensions/asdl-visualizer && npm run build

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- extensions/asdl-visualizer/src/extension/commands.ts
- extensions/asdl-visualizer/src/extension/symbols.ts
- extensions/asdl-visualizer/src/extension/types.ts
- extensions/asdl-visualizer/src/webview/app.tsx
- extensions/asdl-visualizer/src/webview/styles.css

# Plan
- Review visualizer extension types, symbol loading, and webview rendering.
- Update glyph resolution and diagnostics in extension, and glyph rendering in webview.
- Verify build and update task state + PR.

# Progress log
- 2026-01-27 00:00 — Task intake and context review; read role/contract/tasks; created scratchpad; next step update task state/branch.
- 2026-01-27 00:01 — Set T-236 to in_progress and linted tasks_state; created feature branch; next step inspect visualizer code.
- 2026-01-27 00:02 — Task understanding: resolve glyph assets relative to .asdl, produce webview-safe URIs, render SVGs inside glyph.box with optional viewbox, and emit missing-glyph diagnostics.
- 2026-01-27 00:03 — Committed task kickoff (status + scratchpad) in 617a485; next step implement glyph resolution.
- 2026-01-27 00:15 — Implemented glyph resolution + webview-safe URIs with diagnostics and webview roots; committed as acbf96f; next step render glyphs in webview.
- 2026-01-27 00:24 — Added glyph rendering + CSS positioning in webview; committed as 5ce1cf5; next step run build.
- 2026-01-27 00:32 — Ran npm run build in extensions/asdl-visualizer; success with Vite CJS deprecation warning; next step update scratchpad summary and task state.

# Patch summary
- Resolve glyph sources relative to .asdl files, convert to webview URIs, and emit diagnostics on missing assets.
- Add webview resource roots for visualizer glyph directories.
- Render glyph SVGs in instance nodes using glyph.box coordinates and preserve aspect ratio.

# PR URL
https://github.com/Jianxun/ASDL/pull/249
# Verification
- cd extensions/asdl-visualizer && npm run build (passes; Vite CJS deprecation warning)

# Status request
- Ready for review

# Blockers / Questions
- None.

# Next steps
- Await reviewer feedback.
- 2026-01-27 00:40 — Opened PR https://github.com/Jianxun/ASDL/pull/249; set T-236 ready_for_review with pr 249; next step await review.
