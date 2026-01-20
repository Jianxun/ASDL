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
- [ ] Identify axis helper boundaries + public API.
- [ ] Move helpers to new module and update imports.
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
- Start extracting axis helper module.
