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
- [x] Update `spec_ast.md` delimiter notes and examples to use `<...>`.
- [x] Update `spec_asdl_pattern_expansion.md` for `<start:end>` ranges and enum examples.
- [x] Confirm no legacy `[]` ranges remain in the specs.
- [ ] Open PR and finalize task status.

# Progress log
- 2026-01-19: Initialized scratchpad and set task to in progress.
- 2026-01-19: Updated spec delimiter text/examples and ran verification.

# Patch summary
- Updated pattern delimiter references and examples to use `<start:end>` ranges and `<...>` enums.
- Added an enum example for `<digits>` and aligned enum delimiter examples.

# PR URL
- TBD

# Verification
- `rg -n "\\[[0-9]+:[0-9]+\\]" docs/specs/spec_ast.md docs/specs/spec_asdl_pattern_expansion.md` (no matches)

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None.

# Next steps
- Open PR and request review once commits are ready.
