# Task summary (DoD + verify)
- Add a core dataclass model for fully-atomized graphs (program, module, net, instance, endpoint) including stable IDs, resolved atom names, and optional provenance back-references to PatternedGraph entities. Document the model in a refactor spec and export it from `asdl.core`.
- Verify: `venv/bin/python -m py_compile src/asdl/core/atomized_graph.py`

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- [x] Review existing PatternedGraph model for naming/ID conventions.
- [x] Define atomized core dataclasses with stable IDs and provenance references.
- [x] Document the AtomizedGraph model in the refactor spec and export from `asdl.core`.
- [x] Run the task verification command.

# Progress log
- Added AtomizedGraph dataclasses and core exports.
- Documented the AtomizedGraph model and verified module compilation.

# Patch summary
- Added AtomizedGraph dataclasses and exports in core.
- Added refactor spec for AtomizedGraph.

# PR URL
- https://github.com/Jianxun/ASDL/pull/201

# Verification
- `venv/bin/python -m py_compile src/asdl/core/atomized_graph.py`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None.

# Next steps
- Implement the AtomizedGraph dataclass model and documentation.
