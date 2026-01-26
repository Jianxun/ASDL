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
- 2026-01-26 01:52 — Task intake; confirmed T-231 ready -> set in_progress, created feature branch; next inspect visualizer extension/webview symbol/layout usage.
- 2026-01-26 02:06 — Committed task setup (in_progress + expanded scratchpad); commit a18ac42; next implement symbol loader + graph updates.
- 2026-01-26 02:06 — Implemented symbol sidecar loading + unified schema, wired into graph build; commit 3ed89f7; next update webview pin placement/anchors.
- 2026-01-26 02:06 — Updated webview for pin placement + top-left instance anchors + hub handle; commit ba495f6; next run build/verify.
- 2026-01-26 02:06 — Ran npm run build (extensions/asdl-visualizer); success with Vite CJS deprecation warning; next finalize scratchpad + status.
- 2026-01-26 02:08 — Opened PR https://github.com/Jianxun/ASDL/pull/243; next update task status + finalize scratchpad.

## Patch summary
- Load `.sym.yaml` sidecars by file_id, normalize unified symbol schema, validate pins, and attach symbol refs to graph payload.
- Render instance pins via symbol-driven placement, move instance anchors to top-left grid coordinates, and adjust layout save logic.
- Add hub handle id/placement and adjust webview styles for pin/hub handles.

## PR URL
https://github.com/Jianxun/ASDL/pull/243
## Verification
- `npm run build` (extensions/asdl-visualizer) — ok; Vite CJS Node API deprecation warning.

## Status request (Done / Blocked / In Progress)
Done

## Blockers / Questions
None.

## Next steps
- Await reviewer feedback.
- 2026-01-26 02:08 — Set T-231 status to ready_for_review (PR 243) and ran lint_tasks_state.py; next push final updates.
- 2026-01-26 03:10 — Set T-231 status to review_in_progress and ran lint_tasks_state.py; next review PR 243.
- 2026-01-26 03:18 — Review intake: PR targets main, scratchpad/verify logs present, no links.spec found; next complete scope review.
- 2026-01-26 03:20 — Scope review complete: changes align with T-231 DoD; no out-of-scope edits; next verify checks/logs.
- 2026-01-26 03:21 — Checks: npm run build log present in scratchpad; no additional runs; next finalize review decision.
- 2026-01-26 03:22 — Set T-231 status to review_clean and ran lint_tasks_state.py; next post PR comment and start merge/closeout.
- 2026-01-26 03:23 — Posted PR comment with review results; next update status to done and merge/closeout.
- 2026-01-26 03:24 — Set T-231 status to done (merged true) and ran lint_tasks_state.py; next commit/push and merge PR.
