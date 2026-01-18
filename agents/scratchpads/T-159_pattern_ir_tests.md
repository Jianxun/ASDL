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
- [x] Review GraphIR lowering and IFIR delimiter checks for pattern detection.
- [x] Update delimiter detection to remove `[`/`]` and rely on `<`, `>`, `|`, `;`.
- [x] Refresh IR unit tests and expected pattern_origin strings for `<start:end>` ranges.
- [x] Run targeted IR tests.
- [ ] Open PR and finalize task status.

# Progress log
- 2026-01-19: Initialized scratchpad and set task to in progress.
- 2026-01-19: Updated IR tests to use `<start:end>` ranges and refreshed pattern origin strings.
- 2026-01-19: Updated GraphIR lowering + IFIR delimiter checks to drop `[]` and include `|`.
- 2026-01-19: Ran IR unit tests for pattern engine and IFIR dialect.
- 2026-01-19: Opened PR #165.

# Patch summary
- Updated IR unit tests to use `<start:end>` ranges and adjusted pattern_origin expectations.
- Updated GraphIR lowering and IFIR delimiter detection to drop `[`/`]` and include `|`.

# PR URL
- https://github.com/Jianxun/ASDL/pull/165

# Verification
- `venv/bin/pytest tests/unit_tests/ir/test_pattern_engine.py tests/unit_tests/ir/test_ifir_dialect.py -v`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None.

# Next steps
- Await review feedback.
