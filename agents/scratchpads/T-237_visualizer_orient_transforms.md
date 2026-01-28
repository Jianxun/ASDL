# Task summary (DoD + verify)
- DoD: Implement `orient` transforms for instance nodes (R0/R90/R180/R270/MX/MY/MXR90/MYR90) following Cadence Virtuoso orientation semantics with R90 as counter-clockwise rotation about the symbol's top-left origin, and mirror operations applied before rotation. Use a consistent mirror system for screen coords (x→right, y→down) and define it in code/spec. Update pin geometry to respect orientation, swap body dimensions when rotated, and move the hub handle to the oriented side with hub transforms about the hub center (single movable handle).
- Verify: `cd extensions/asdl-visualizer && npm run build`

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect current symbol orientation handling in visualizer webview.
- Implement orient transform helpers and update geometry/pin/hub handling.
- Update styles/spec if required by DoD.
- Run build verify.

# Progress log
- 2026-01-27 21:10 — Task intake; reviewed contract/spec/tasks; noted existing in-progress status; next step: inspect visualizer webview orientation handling.
- 2026-01-27 21:10 — Ran task state lint (./venv/bin/python scripts/lint_tasks_state.py); OK; next step: implement orient transforms.
- 2026-01-27 21:19 — Started implementing orient transform helpers and applying to instance/hub geometry in webview; next step: adjust app.tsx and commit.
- 2026-01-27 21:20 — Commit 1c5d76c (chore: start T-237 orient transforms); updated tasks_state and scratchpad; next step: finish app.tsx orient logic.
- 2026-01-27 21:19 — Implemented orientation helpers, oriented body/pin geometry, and hub handle placement in webview; files touched: extensions/asdl-visualizer/src/webview/app.tsx; next step: commit changes.
- 2026-01-27 21:20 — Commit 68a25ea (feat: apply visualizer orient transforms); next step: run visualizer build.
- 2026-01-27 21:21 — Verification: cd extensions/asdl-visualizer && npm run build (success; Vite CJS deprecation warning only).
- 2026-01-27 21:21 — Commit 5e1d7d2 (chore: update T-237 scratchpad); next step: open PR.
- 2026-01-27 21:21 — Opened PR https://github.com/Jianxun/ASDL/pull/250; next step: update tasks_state.
- 2026-01-27 21:21 — Set T-237 status to ready_for_review with PR 250; ran ./venv/bin/python scripts/lint_tasks_state.py; next step: final push.

# Patch summary
- Added Cadence-style orientation helpers for mirrors/rotations and applied them to instance body sizing, pin placement, glyph box placement, and hub handle positioning in the visualizer webview.

# PR URL
- https://github.com/Jianxun/ASDL/pull/250

# Verification
- cd extensions/asdl-visualizer && npm run build

# Status request (Done / Blocked / In Progress)
- Ready for review

# Blockers / Questions
- None.

# Next steps
- Await reviewer feedback.
