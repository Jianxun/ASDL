# T-322 Scratchpad

## Task summary (DoD + verify)
- DoD: add module-level `parameters` as first-class data in AST `ModuleDecl`,
  PatternedGraph module bundles/builders, and AtomizedGraph module
  dataclasses/lowering; reuse existing `parameters` naming/value conventions and
  avoid `params` aliases; add regressions proving parse/lower/atomize and
  deterministic key order retention.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/core/test_patterned_graph_builder.py tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/core/test_patterned_graph_atomize.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/ast/models.py`
- `src/asdl/core/graph.py`
- `src/asdl/core/atomized_graph.py`
- `src/asdl/core/graph_builder.py`
- `src/asdl/lowering/ast_to_patterned_graph.py`
- `src/asdl/lowering/patterned_graph_to_atomized.py`
- `tests/unit_tests/ast/test_models.py`
- `tests/unit_tests/core/test_patterned_graph_builder.py`
- `tests/unit_tests/core/test_patterned_graph_lowering.py`
- `tests/unit_tests/core/test_patterned_graph_atomize.py`

## Plan
1. Add failing tests for AST + builder/lowering + atomization module-parameter
   threading.
2. Implement minimal production changes in AST/core/lowering paths.
3. Run required verify suite and ensure deterministic behavior is covered.
4. Close out with task-state + PR handoff.

## Milestone notes
- Intake: confirmed `T-322` status `ready`; moved to `in_progress`; linted state.
- Reuse audit: reused existing `parameters` field patterns already used for
  devices/backends/instances; extended module paths without adding alias fields.
- TDD red: added regressions and observed expected failures in AST parse/model,
  builder module signature, and PatternedGraph/AtomizedGraph module data
  propagation.
- TDD green: threaded module parameters through AST model, PatternedGraph
  dataclasses/builder/lowering, and PatternedGraph->AtomizedGraph lowering.
- Verification: required pytest suite passed.

## Patch summary
- Added `ModuleDecl.parameters` as canonical module-level parameter map.
- Added `parameters` to `ModuleGraph` and `AtomizedModuleGraph` dataclasses.
- Extended `PatternedGraphBuilder.add_module(..., parameters=...)`.
- Passed module parameters through AST->PatternedGraph lowering (single-file and
  import-graph paths).
- Propagated module parameters through PatternedGraph->AtomizedGraph lowering.
- Added regression tests proving AST parse support and end-to-end
  module-parameter propagation across builder/lowering/atomization.

## PR URL
- Pending PR creation

## Verification
- `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/core/test_patterned_graph_builder.py tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/core/test_patterned_graph_atomize.py -v` (pass, 83 passed)

## Status request
- Ready for review after PR creation and task-state update.

## Blockers / Questions
- None.

## Next steps
- Push branch, open PR to `main`, set `T-322` to `ready_for_review` with PR number.
