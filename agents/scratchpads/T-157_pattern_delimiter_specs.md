# Task summary (DoD + verify)
- DoD: Replace numeric range syntax `[...]` with `<start:end>` in `docs/specs/spec_ast.md` and `docs/specs/spec_asdl_pattern_expansion.md`, update delimiter descriptions to remove `[]`, and add/adjust examples to show `<...>` for enums and ranges (including the `<digits>` enum case).
- Verify: `rg -n "\\[[0-9]+:[0-9]+\\]" docs/specs/spec_ast.md docs/specs/spec_asdl_pattern_expansion.md`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- Update spec language and examples to use `<start:end>` ranges and `<...>` enums.
- Confirm no remaining legacy `[]` ranges with ripgrep verify command.
- Record changes, verification, and status in this scratchpad.

# Progress log
- 2026-01-19: Initialized scratchpad and starting updates.

# Patch summary
- TBD

# PR URL
- TBD

# Verification
- TBD

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None.

# Next steps
- Update specs and run verify command.
