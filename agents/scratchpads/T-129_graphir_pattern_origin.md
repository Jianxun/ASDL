# T-129 GraphIR pattern origin attributes and table

## Objective
- Add typed `graphir.pattern_origin` attr, attach to net/instance/endpoint ops.
- Define module attrs `pattern_expression_table` and document in spec.

## Notes
- pattern_origin fields: expression_id, segment_index (0-based), base_name,
  pattern_parts.

## Files
- src/asdl/ir/graphir/attrs.py
- src/asdl/ir/graphir/ops_graph.py
- src/asdl/ir/graphir/ops_module.py
- docs/specs/spec_asdl_graphir.md
