# Task summary (DoD + verify)
- DoD: Move tagged-axis analysis helpers from ast_to_graphir_lowering_nets.py into a dedicated module, update imports/callers, and keep diagnostics behavior identical. Public helpers must keep or add docstrings.
- Verify: venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/ir/converters/ast_to_graphir_lowering_nets.py

# Plan
- [x] Identify axis helper boundaries + public API.
- [x] Move helpers to new module and update imports.
- [x] Run targeted GraphIR converter tests.

# Progress log
- 2026-01-20: Created scratchpad.
- 2026-01-20: Extracted tagged-axis helpers into dedicated module.
- 2026-01-20: Verified GraphIR converter unit tests.
- 2026-01-20: Opened PR #174.

# Patch summary
- Added `src/asdl/ir/converters/ast_to_graphir_axis.py` for tagged-axis helpers.
- Updated `src/asdl/ir/converters/ast_to_graphir_lowering_nets.py` to import helpers.

# PR URL
- https://github.com/Jianxun/ASDL/pull/174

# Verification
- `venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None yet.

# Next steps
- Start extracting axis helper module.
