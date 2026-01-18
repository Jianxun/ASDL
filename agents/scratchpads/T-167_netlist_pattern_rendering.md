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
- [x] Inspect netlist emission name rendering for pattern origin usage.
- [x] Add pattern origin rendering helper using backend pattern policy.
- [x] Update netlist emission to use rendered names for nets/instances.
- [x] Add tests for bracketed numeric indices in emitted netlists.

# Progress log
- 2026-xx-xx: Created scratchpad and loaded task context.
- 2026-xx-xx: Understanding: use pattern_origin + backend pattern rendering for net/instance display names in netlist output.
- 2026-xx-xx: Added netlist test for bracketed numeric indices.
- 2026-xx-xx: Implemented pattern-origin rendering in netlist emission and pattern helpers.
- 2026-xx-xx: Verified netlist emitter tests.

# Patch summary
- Added pattern-origin rendering helper to format numeric parts using backend policy.
- Updated netlist emission to render instance/net names with pattern provenance.
- Added netlist emitter coverage for bracketed numeric indices.

# PR URL

# Verification
- `venv/bin/pytest tests/unit_tests/netlist/test_netlist_emitter.py -v`

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions

# Next steps
