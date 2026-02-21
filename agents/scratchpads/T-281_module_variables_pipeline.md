# T-281 - module variables pipeline propagation

## Task summary (DoD + verify)
- DoD: Preserve `module.variables` beyond AST parsing by threading module variable maps through PatternedGraph/AtomizedGraph data models and lowering paths so later substitution stages can consume them deterministically.
- Verify: `./venv/bin/pytest tests/unit_tests/core tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/core/graph.py`
- `src/asdl/core/atomized_graph.py`
- `src/asdl/core/graph_builder.py`
- `src/asdl/lowering/ast_to_patterned_graph.py`
- `src/asdl/lowering/patterned_graph_to_atomized.py`
- `tests/unit_tests/core/test_patterned_graph_lowering.py`
- `tests/unit_tests/core/test_patterned_graph_atomize.py`

## Plan
1. Add regression tests that assert module-level variables are preserved in PatternedGraph and AtomizedGraph.
2. Extend graph model dataclasses and builder APIs to carry module variables.
3. Thread module variables through AST->PatternedGraph and PatternedGraph->AtomizedGraph lowering.
4. Run task verify suite and close out task state.

## Milestone notes
- 2026-02-21: Intake complete; task `T-281` moved to `in_progress` and role workflow applied.
- 2026-02-21: Added failing tests first for module variables propagation.
- 2026-02-21: Implemented model/builder/lowering propagation and re-ran targeted + full verify suite.

## Patch summary
- Added `variables` field to `ModuleGraph` and `AtomizedModuleGraph`.
- Updated `PatternedGraphBuilder.add_module(...)` to accept and store module variables.
- Updated AST lowering to pass `module.variables` into module graph creation (single-file and import-graph paths).
- Updated PatternedGraph->AtomizedGraph lowering to propagate module variables unchanged.
- Added regression tests:
  - `test_build_patterned_graph_preserves_module_variables`
  - `test_patterned_graph_atomize_propagates_module_variables`

## PR URL
- https://github.com/Jianxun/ASDL/pull/304

## Verification
- `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py::test_build_patterned_graph_preserves_module_variables tests/unit_tests/core/test_patterned_graph_atomize.py::test_patterned_graph_atomize_propagates_module_variables -v` (pass)
- `./venv/bin/pytest tests/unit_tests/core tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py -v` (pass, 47 passed)

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
- Reviewer validates no downstream assumptions on module-variable mutability before T-282 substitution logic lands.
