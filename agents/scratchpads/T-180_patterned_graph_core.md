# Task summary (DoD + verify)
- Implement dataclass-based ProgramGraph/ModuleGraph/NetBundle/InstanceBundle/EndpointBundle plus registry types (PatternExpressionRegistry, SourceSpanIndex, SchematicHints).
- Add tests covering construction, endpoint ownership, and registry optionality.
- Verify: venv/bin/pytest tests/unit_tests/core/test_patterned_graph.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- [ ] Review spec and existing patterns/diagnostics helpers to align types and IDs.
- [ ] Add tests for construction, endpoint ownership, and registry optionality.
- [ ] Implement core dataclasses + registries and exports.
- [ ] Run verification and capture results.

# Progress log
- Added tests for construction, endpoint ownership, and registry optionality.
- Implemented core dataclasses/registries and exported them from `asdl.core`.
- Ran the targeted pytest command.

# Patch summary
- agents/context/tasks_state.yaml: set T-180 to in_progress.
- agents/scratchpads/T-180_patterned_graph_core.md: initialize task scratchpad.
- src/asdl/core/graph.py + src/asdl/core/registries.py + src/asdl/core/__init__.py: add PatternedGraph core dataclasses and registries.
- tests/unit_tests/core/test_patterned_graph.py: add coverage for construction, endpoint ownership, and registry optionality.

# PR URL
- 

# Verification
- ./venv/bin/pytest tests/unit_tests/core/test_patterned_graph.py -v

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- 

# Next steps
- 
