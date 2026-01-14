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
- [x] Inspect existing GraphIR dialect/ops and converter patterns.
- [x] Write fixture + unit tests for single-file conversion.
- [x] Implement converter with diagnostics and stable IDs; run tests.

## Progress log
- 2026-01-13: Clarified task scope (single-doc AST -> GraphIR with diagnostics/IDs) and created setup commit.
- 2026-01-13: Added fixture-based tests for GraphIR conversion + unresolved symbol diagnostics.
- 2026-01-13: Implemented AST -> GraphIR converter with stable IDs and ran tests.

## Patch summary
- `src/asdl/ir/converters/ast_to_graphir.py`: implement single-document GraphIR conversion with diagnostics and stable IDs.
- `tests/unit_tests/ir/test_graphir_converter.py`: add fixture-based conversion + unresolved symbol tests.
- `tests/unit_tests/ir/fixtures/graphir_single_file.asdl`: add single-file conversion fixture.

## PR URL
- https://github.com/Jianxun/ASDL/pull/123

## Verification
- `venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v`

## Status request
- Ready for Review

## Blockers / Questions
- 

## Next steps
- Await review feedback.
