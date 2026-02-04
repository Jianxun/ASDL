# Task summary (DoD + verify)
- DoD: Allow visualizer command when active editor is .asdl or .sch.yaml, resolving companion .asdl. Add keybinding matching Markdown preview (Cmd/Ctrl+Shift+V) without conflicting with existing ASDL commands. Update extension contribution metadata and document new launch behavior.
- Verify: npm --prefix extensions/asdl-visualizer run build:extension

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect extension command activation/launch logic and existing keybindings.
- Implement .sch.yaml handling + companion resolution.
- Add keybinding contribution without conflicts.
- Update docs/specs for launch behavior.
- Verify build.

# Milestone notes
- Todo:
  - [x] Update visualizer launch resolution for .sch.yaml.
  - [x] Add command palette/keybinding metadata.
  - [x] Document launch behavior.
  - [x] Run build:extension verification.

# Patch summary
- Updated visualizer launch logic to accept .sch.yaml editors with companion .asdl resolution.
- Added Cmd/Ctrl+Shift+V keybinding and .sch.yaml palette visibility.
- Documented launch behavior and hotkey in extension spec.

# PR URL

# Verification
- npm --prefix extensions/asdl-visualizer run build:extension

# Status request (Done / Blocked / In Progress)
Done

# Blockers / Questions

# Next steps
