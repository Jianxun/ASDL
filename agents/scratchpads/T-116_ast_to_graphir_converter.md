# T-116 AST to GraphIR converter

## Task summary (DoD + verify)
- Implement AST -> GraphIR converter for a single document with resolved local symbols.
- Convert modules, devices, nets, instances, and endpoints into GraphIR ops with stable IDs and port_order.
- Emit diagnostics for unresolved references.
- Add unit tests for a single-file fixture.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`

## Plan
- Inspect existing GraphIR dialect/ops and any converter scaffolding.
- Write test fixture + unit tests to encode single-file conversion expectations.
- Implement converter with diagnostics, then re-run tests.

## Progress log
- 2026-01-xx: Set task to in_progress, created feature branch, initialized scratchpad.

## Patch summary
- 

## PR URL
- 

## Verification
- 

## Status request
- In Progress

## Blockers / Questions
- 

## Next steps
- Inspect existing GraphIR ops and current AST/NFIR converters for reference.
