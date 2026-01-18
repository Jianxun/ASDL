# Task summary (DoD + verify)
- DoD: Render net/instance names using pattern provenance metadata and the backend pattern rendering policy, and add netlist emission tests covering bracketed numeric indices.
- Verify: venv/bin/pytest tests/unit_tests/netlist/test_netlist_emitter.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Review netlist emission name rendering and pattern origin helpers.
- Implement pattern-based name rendering with backend numeric formatting.
- Add netlist emission tests for bracketed numeric indices.
- Verify targeted netlist tests and update scratchpad.

# Todo
- [ ] Inspect netlist emission name rendering for pattern origin usage.
- [ ] Add pattern origin rendering helper using backend pattern policy.
- [ ] Update netlist emission to use rendered names for nets/instances.
- [ ] Add tests for bracketed numeric indices in emitted netlists.

# Progress log
- 2026-xx-xx: Created scratchpad and loaded task context.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions

# Next steps
