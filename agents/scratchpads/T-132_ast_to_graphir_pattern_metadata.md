# T-132 AST to GraphIR pattern metadata integration

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
