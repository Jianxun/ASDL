# Task summary (DoD + verify)
- DoD: Extend PatternedGraph and AtomizedGraph core dataclasses with device definitions (stable ID, name, file_id, ports list, optional params/vars/attrs). Replace module port_order with a canonical ports list (empty list allowed, never None) and add builder support for devices/ports while preserving compatibility for existing callers.
- Verify: venv/bin/python -m py_compile src/asdl/core/graph.py src/asdl/core/atomized_graph.py src/asdl/core/graph_builder.py src/asdl/core/__init__.py

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect core graph/atomized graph dataclasses and builders for port/device shapes.
- Update dataclasses for ports/device definitions with required fields and defaults.
- Update builder APIs to accept devices/ports with backward compatibility.
- Adjust exports/init and any dependent code minimally.
- Run verify command and record results.

# Progress log
- 2026-01-23: Initialized scratchpad.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
