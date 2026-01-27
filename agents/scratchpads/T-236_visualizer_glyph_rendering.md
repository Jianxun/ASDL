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

# Plan
- Review visualizer extension types, symbol loading, and webview rendering.
- Update glyph resolution and diagnostics in extension, and glyph rendering in webview.
- Verify build and update task state + PR.

# Progress log

# Patch summary

# PR URL

# Verification

# Status request

# Blockers / Questions

# Next steps
# Progress log
- 2026-01-27 00:00 — Task intake and context review; read role/contract/tasks; created scratchpad; next step update task state/branch.
- 2026-01-27 00:01 — Set T-236 to in_progress and linted tasks_state; created feature branch; next step inspect visualizer code.

Task understanding: wire glyph asset resolution in the extension so glyph.src paths are resolved relative to the source .asdl file, turned into a webview-safe URI, and passed through payload; then update webview rendering to draw the SVG within the schema-defined glyph.box (grid units) preserving aspect ratio and honoring optional viewbox metadata; emit diagnostics if glyph resolution fails.
