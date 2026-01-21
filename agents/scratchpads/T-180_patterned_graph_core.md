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
- [x] Review spec and existing patterns/diagnostics helpers to align types and IDs.
- [x] Add tests for construction, endpoint ownership, and registry optionality.
- [x] Implement core dataclasses + registries and exports.
- [x] Run verification and capture results.

# Progress log
- Added tests for construction, endpoint ownership, and registry optionality.
- Implemented core dataclasses/registries and exported them from `asdl.core`.
- Ran the targeted pytest command.
- Added AnnotationIndex and RegistrySet.annotations; updated optionality coverage.

# Patch summary
- agents/context/tasks_state.yaml: set T-180 to in_progress.
- agents/scratchpads/T-180_patterned_graph_core.md: initialize task scratchpad.
- src/asdl/core/graph.py + src/asdl/core/registries.py + src/asdl/core/__init__.py: add PatternedGraph core dataclasses and registries.
- tests/unit_tests/core/test_patterned_graph.py: add coverage for construction, endpoint ownership, and registry optionality.
- src/asdl/core/registries.py + src/asdl/core/__init__.py: add AnnotationIndex and RegistrySet.annotations support.
- tests/unit_tests/core/test_patterned_graph.py: assert annotations registry optionality.

# PR URL
- https://github.com/Jianxun/ASDL/pull/182

# Verification
- ./venv/bin/pytest tests/unit_tests/core/test_patterned_graph.py -v
- ./venv/bin/pytest tests/unit_tests/core/test_patterned_graph.py -v

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- 

# Next steps
- Await review feedback.
