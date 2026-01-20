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
- [ ] Identify shared explicit-net prep/mapping logic.
- [ ] Add helper functions and refactor explicit-net flow.
- [ ] Run targeted GraphIR converter tests.

# Progress log
- 2026-01-20: Created scratchpad.

# Patch summary
- None yet.

# PR URL
- None yet.

# Verification
- Not run yet.

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None yet.

# Next steps
- Wait for T-173 completion, then start explicit-net refactor.
