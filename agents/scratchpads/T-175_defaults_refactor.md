# Task summary (DoD + verify)
- DoD: Apply the shared net-prep and endpoint-mapping helpers to the instance-defaults path and reduce duplicated if/else blocks while keeping diagnostics identical.
- Verify: venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/ir/converters/ast_to_graphir_lowering_nets.py

# Plan
- [x] Identify default-net flow that can reuse shared helpers.
- [x] Refactor instance-defaults lowering to call shared helpers.
- [x] Run targeted GraphIR converter tests.

# Progress log
- 2026-01-20: Created scratchpad.
- 2026-01-20: Refactored instance-defaults lowering to reuse helpers and ran tests.

# Patch summary
- Reused shared net preparation and endpoint mapping helpers for instance defaults.
- Preserved diagnostic behavior while reducing duplicated mapping logic.

# PR URL
- https://github.com/Jianxun/ASDL/pull/176

# Verification
- venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None yet.

# Next steps
- Await review.
