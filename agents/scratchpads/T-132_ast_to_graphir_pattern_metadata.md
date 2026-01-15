# T-132 AST to GraphIR pattern metadata integration

## Task summary (DoD + verify)
- Update AST->GraphIR conversion to register pattern expression table entries,
  attach pattern_origin metadata to atomized nets/instances/endpoints and
  instance params, and expand endpoint expressions as a whole before splitting
  on '.'.
- Endpoint resolution must operate on expanded atoms so subset bindings like
  MN_IN_<N>.D match atomized instances.
- Binding length checks compare pattern expression expansion lengths for nets
  vs endpoints (exact match).
- Patterned params expand after instance expansion with scalar broadcast or
  exact-length zip.
- Emit diagnostics for expansion collisions and length mismatches.
- Add unit tests covering subset bindings and failure cases. Binding logic
  remains in ast_to_graphir.py.
- Verify: venv/bin/pytest tests/unit_tests/ir -v

## Objective
- Attach pattern_origin metadata and module expression table entries during
  AST->GraphIR conversion, enabling subset pattern bindings by resolving
  expanded endpoint atoms against atomized instances.

## Notes
- Expand endpoint expressions as a whole, then split on `.`.
- Keep binding logic in ast_to_graphir.py.
- Subset bindings should resolve via expansion (e.g., `MN_IN_<N>.D` →
  `MN_IN_N.D`) after instance atomization.
- Binding length checks compare pattern expression expansion lengths (exact
  match) for nets vs endpoints.
- Patterned params expand after instance expansion with scalar broadcast or
  exact-length zip.
- $ nets allow pattern expansion but reject splice delimiters (`;`).
- Add diagnostics for pattern collisions and length mismatches.
- Tests: add subset-binding coverage plus negative cases in
  `tests/unit_tests/ir`.

## Files
- src/asdl/ir/converters/ast_to_graphir.py
- src/asdl/ir/patterns/expr_table.py
- src/asdl/ir/patterns/origin.py
- src/asdl/ir/patterns/endpoint_split.py
- src/asdl/ir/graphir/ops_graph.py

## References
- ADR-0011: Pattern atomization before IFIR verification (atomize, preserve origin, collision errors).
- ADR-0012: Endpoint resolution uses atomized literal equivalence.
- ADR-0013: Atomize endpoints per instance; idempotent atomization.
- ADR-0009: Pattern expansion uses literal concatenation; no implicit joiner.
- docs/specs/spec_asdl_pattern_expansion.md
- docs/specs/spec_ast.md

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/ir/converters/ast_to_graphir_lowering.py
- src/asdl/ir/graphir/ops_graph.py
- src/asdl/ir/patterns/*
- tests/unit_tests/ir/test_graphir_converter.py

## Plan
- Add GraphIR converter tests for pattern expansion metadata, subset bindings, and failure cases.
- Expand pattern-aware lowering: atomize names/endpoints, attach origins, register expression table, and enforce length checks.
- Verify with `venv/bin/pytest tests/unit_tests/ir -v`.

## Progress log
- Added unit tests for pattern expansion metadata, subset binding, and diagnostics.
- Implemented pattern-aware GraphIR lowering with pattern expression table, pattern origins, param expansion, and collision/length diagnostics.
- Added InstanceOp param_pattern_origin attribute to carry per-param pattern origins.
- Verified unit tests.

## Patch summary
- tests/unit_tests/ir/test_graphir_converter.py: added pattern expansion, subset binding, and failure coverage.
- src/asdl/ir/converters/ast_to_graphir_lowering.py: expanded patterns for instances/nets/endpoints/params; registered expression table; attached origins; added diagnostics.
- src/asdl/ir/graphir/ops_graph.py: added InstanceOp param_pattern_origin attribute.

## PR URL
- https://github.com/Jianxun/ASDL/pull/145

## Verification
- venv/bin/pytest tests/unit_tests/ir -v

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
