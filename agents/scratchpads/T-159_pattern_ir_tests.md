# Task summary (DoD + verify)
- DoD: Remove `[`/`]` from pattern delimiter detection in GraphIR lowering and IFIR verification so pattern presence is keyed to `<`, `>`, `|`, and `;`, and update IR unit tests to use `<start:end>` with updated pattern_origin strings.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_pattern_engine.py tests/unit_tests/ir/test_ifir_dialect.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- [ ] Review GraphIR lowering and IFIR delimiter checks for pattern detection.
- [ ] Update delimiter detection to remove `[`/`]` and rely on `<`, `>`, `|`, `;`.
- [ ] Refresh IR unit tests and expected pattern_origin strings for `<start:end>` ranges.
- [ ] Run targeted IR tests.
- [ ] Open PR and finalize task status.

# Progress log
- 2026-01-19: Initialized scratchpad and set task to in progress.

# Patch summary
- TBD.

# PR URL
- TBD.

# Verification
- TBD.

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None.

# Next steps
- Update delimiter detection and tests, then run verification.
