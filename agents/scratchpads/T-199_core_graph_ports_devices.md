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
- [x] Inspect core graph/atomized graph dataclasses and builders for port/device shapes.
- [x] Update dataclasses for ports/device definitions with required fields and defaults.
- [x] Update builder APIs to accept devices/ports with backward compatibility.
- [x] Adjust exports/init and any dependent code minimally.
- [x] Run verify command and record results.

# Progress log
- 2026-01-23: Initialized scratchpad.
- 2026-01-23: Added device definitions and ports lists to core graphs with port_order compatibility.
- 2026-01-23: Added device/ports support to graph builder and updated core exports.
- 2026-01-23: Opened PR #204.

# Patch summary
- Added DeviceDef/AtomizedDeviceDef dataclasses, device registries, and canonical ports lists for modules.
- Added builder support for devices and ports with backward-compatible port_order alias.
- Exported new device types in core __init__.

# PR URL
- https://github.com/Jianxun/ASDL/pull/204

# Verification
- `venv/bin/python -m py_compile src/asdl/core/graph.py src/asdl/core/atomized_graph.py src/asdl/core/graph_builder.py src/asdl/core/__init__.py`

# Status request (Done / Blocked / In Progress)
- Ready for review.

# Blockers / Questions

# Next steps

# Review log
- 2026-01-23: Reviewer intake complete; PR #204 targets main and scratchpad/verify command present.
- 2026-01-23: Set status to review_in_progress, linted tasks_state, and ran DoD verify command (py_compile).
- 2026-01-23: Scope review complete; changes align with DoD (device defs + ports list + builder support + compatibility), no out-of-scope spec edits.
- 2026-01-23: Review decision posted as review_clean; no blockers found and verification command passed.
