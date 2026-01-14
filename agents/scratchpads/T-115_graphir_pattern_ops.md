# T-115 GraphIR bundles and pattern_expr ops

## Task summary (DoD + verify)
- Define GraphIR bundle and pattern_expr ops, including ParamRef ownership for
  param patterns. Implement verification for bundle ownership and pattern_expr
  kind/owner alignment and add unit tests for net/endpoint/param pattern
  ownership.
- Verify: venv/bin/pytest tests/unit_tests/ir/test_graphir_patterns.py -v

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs/spec_asdl_graphir.md
- docs/specs/spec_asdl_graphir_schema.md
- src/asdl/ir/graphir/ops_module.py
- src/asdl/ir/graphir/ops_graph.py
- tests/unit_tests/ir/test_graphir_structure.py

## Plan
- Add GraphIR bundle/pattern_expr ops and ParamRef attribute per spec.
- Update module verification for bundle ownership and pattern_expr owners.
- Add tests for net/endpoint/param ownership and bundle ownership.

## Progress log
- Added GraphIR pattern ownership tests (net/endpoint/param + bundle reuse).
- Implemented bundle/pattern_expr ops and ParamRef attr, plus module verification.
- Opened PR #122.

## Patch summary
- Added `graphir.bundle` and `graphir.pattern_expr` ops with ParamRef support in
  `src/asdl/ir/graphir/ops_pattern.py`.
- Extended GraphIR module verification for bundle ownership + owner alignment in
  `src/asdl/ir/graphir/ops_module.py`.
- Added tests for pattern ownership and bundle reuse in
  `tests/unit_tests/ir/test_graphir_patterns.py`.

## PR URL
- https://github.com/Jianxun/ASDL/pull/122

## Verification
- venv/bin/pytest tests/unit_tests/ir/test_graphir_patterns.py -v

## Status request (Done / Blocked / In Progress)
- Done

## Blockers / Questions
- None.

## Next steps
- Await review.
