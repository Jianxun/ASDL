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

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps

- 2026-01-27 21:10 — Task intake; reviewed contract/spec/tasks; noted existing in-progress status; next step: inspect visualizer webview orientation handling.
- 2026-01-27 21:10 — Ran task state lint (./venv/bin/python scripts/lint_tasks_state.py); OK; next step: implement orient transforms.
- 2026-01-27 21:19 — Started implementing orient transform helpers and applying to instance/hub geometry in webview; next step: adjust app.tsx and commit.
