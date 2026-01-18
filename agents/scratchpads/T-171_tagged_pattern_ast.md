# Task summary (DoD + verify)
- DoD: Extend AST models and parsing to accept patterns as strings or objects with {expr, tag}, validate allowed keys and literal tag names, and expose axis_id + source spans for named pattern groups for downstream diagnostics. Keep named pattern macro expansion behavior intact (expr substitution only). Add unit tests covering string vs object patterns, invalid keys/types, and axis_id derivation.
- Verify: venv/bin/pytest tests/unit_tests/ast -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Understand current AST pattern handling, parser location capture, and named pattern expansion.
- Add tests for tagged pattern objects, invalid keys/types, and axis_id derivation.
- Extend AST models, parser location tracking, and named pattern expansion to support tagged pattern objects.
- Verify tests and document results.

# Progress log
- Understanding: add support for pattern entries that are either group-token strings or {expr, tag} objects, ensure tag is a literal name, derive axis_id from tag or pattern name, and carry axis_id spans for diagnostics while keeping named pattern macro substitution using expr only.
- Todo:
  - [ ] Add tests for tagged pattern entries + axis_id derivation
  - [ ] Update AST models/validators for pattern objects + axis_id helpers
  - [ ] Update parser location capture for pattern expr/tag spans
  - [ ] Update named pattern macro expansion to use expr strings
  - [ ] Run ast unit tests

# Patch summary
- (pending)

# PR URL
- (pending)

# Verification
- (pending)

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None

# Next steps
- (pending)
