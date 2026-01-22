# T-195 Rename and split AST->PatternedGraph lowering

## Task summary (DoD + verify)
- DoD: Rename `src/asdl/lowering/patterned_graph.py` to `src/asdl/lowering/ast_to_patterned_graph.py`. Split orchestration, expression parsing, instance lowering, net/endpoint lowering, and diagnostics helpers into focused lowering modules. Update `asdl.lowering` exports and tests to use the new module name. Preserve diagnostics, ordering, and registry behavior.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [ ] Inspect current patterned graph lowering module and tests to understand responsibilities.
- [ ] Extract helpers into new lowering modules and refactor orchestration.
- [ ] Rename the lowering module and update exports/imports.
- [ ] Run verify command and record results.

## Progress log
- 2026-01-XX: Initialized scratchpad and began splitting lowering helpers.
- 2026-01-XX: Renamed lowering module and updated exports.

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request
- In Progress

## Blockers / Questions
- None yet.

## Next steps
- Review current lowering code and plan split boundaries.
