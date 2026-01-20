# Task summary (DoD + verify)
- DoD: Introduce small helpers for net-pattern preparation and endpoint mapping in the explicit-net path, and flatten the control flow without changing diagnostics or outputs.
- Verify: venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/ir/converters/ast_to_graphir_lowering_nets.py

# Plan
- [x] Refactor explicit-net prep and endpoint mapping into helpers.
- [x] Verify GraphIR converter tests.

# Progress log
- 2026-01-20: Created scratchpad.
- 2026-01-20: Task started; reviewing explicit-net lowering flow.
- 2026-01-20: Refactored explicit-net lowering helpers and verified tests.

# Patch summary
- Added explicit-net helper utilities for net preparation and endpoint mapping.
- Flattened explicit-net lowering flow to use helpers without behavior change.

# PR URL
- https://github.com/Jianxun/ASDL/pull/175

# Verification
- ./venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None yet.

# Next steps
- Await review.
