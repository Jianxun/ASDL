# Task summary (DoD + verify)
- DoD: Move `src/asdl/ir/pattern_atomization.py` and `src/asdl/ir/pattern_elaboration.py` into a new `src/asdl/ir/patterns/` package (e.g., `atomization.py`, `elaboration.py`), update imports in the pipeline/tests, and add a minimal package `__init__.py` export. Keep behavior and diagnostics unchanged.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_pattern_atomization.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- Inspect existing pattern pass modules and import sites.
- Relocate files under `src/asdl/ir/patterns/` and update imports/exports.
- Update tests and codebase map, then verify.

# Progress log
- 2026-02-??: Initialized scratchpad.

# Patch summary
- (pending)

# PR URL
- (pending)

# Verification
- (pending)

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None.

# Next steps
- Inspect current pattern pass modules and update pipeline imports.
