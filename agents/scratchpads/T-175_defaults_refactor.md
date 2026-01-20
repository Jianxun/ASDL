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
- [ ] Identify default-net flow that can reuse shared helpers.
- [ ] Refactor instance-defaults lowering to call shared helpers.
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
- Wait for T-174 completion, then refactor instance-defaults lowering.
