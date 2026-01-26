# T-231: Symbol loading + pin placement + top-left instance anchors

## Task summary (DoD + verify)
- Load `design.sym.yaml` for module/device symbols via `file_id` refs from the visualizer dump.
- Implement unified symbol schema (body, pins, optional glyph, pin_offsets).
- Apply pin placement rules with floor-biased centering and 1-grid spacing.
- Use top-left anchors for instance layout; keep hubs center-based.
- Update React Flow nodes/handles and save path accordingly.
- Verify: `npm run build`.

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/scratchpads/T-231_visualizer_symbols.md

## Plan
- Inspect visualizer extension + webview symbol/layout code and current dump schema usage.
- Define unified symbol schema + loader for `design.sym.yaml` keyed by `file_id`.
- Implement pin placement + top-left anchoring adjustments in layout/render.
- Update webview React Flow nodes/handles to use symbol pin geometry.
- Add/adjust tests if present; run `npm run build`.

## Progress log

## Patch summary

## PR URL

## Verification

## Status request (Done / Blocked / In Progress)

## Blockers / Questions

## Next steps
- 2026-01-26 01:52 — Task intake; confirmed T-231 ready -> set in_progress, created feature branch; next inspect visualizer extension/webview symbol/layout usage.
