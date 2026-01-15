# T-132 AST to GraphIR pattern metadata integration

## Objective
- Attach pattern_origin metadata and module expression table entries during
  AST->GraphIR conversion.

## Notes
- Expand endpoint expressions as a whole, then split on `.`.
- Keep binding logic in ast_to_graphir.py.

## Files
- src/asdl/ir/converters/ast_to_graphir.py
- src/asdl/ir/patterns/expr_table.py
- src/asdl/ir/patterns/origin.py
- src/asdl/ir/patterns/endpoint_split.py
- src/asdl/ir/graphir/ops_graph.py
