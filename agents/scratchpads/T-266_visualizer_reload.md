# Task summary (DoD + verify)
- DoD: Add a reload control in the visualizer webview that re-reads the companion .sym.yaml/.sch.yaml files and refreshes the rendered graph without closing the view. The action should request a reload from the extension host and preserve the current pan/zoom if possible. Document the reload affordance in the visualizer spec or extension README.
- Verify: npm --prefix extensions/asdl-visualizer run build

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Review visualizer extension/webview message flow and current reload behavior.
- Add reload control + message path to extension host and preserve pan/zoom.
- Update documentation and run verify.
- Todo:
  - Implement reload messaging + module reuse in extension.
  - Add reload control + viewport preservation in webview.
  - Document reload affordance and verify build.

# Milestone notes
- Intake complete.

# Patch summary

# PR URL

# Verification

# Status request
- In Progress

# Blockers / Questions
- None.

# Next steps
- Implement reload control + extension request, then document + verify.
