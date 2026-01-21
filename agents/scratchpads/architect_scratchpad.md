# Architect Scratchpad

## Architecture notes (session summary; not yet ADRs)

GraphIR core:
- Move GraphIR to dataclass-based core model; pydantic stays on AST only.
- Drop xDSL textual IR and pass pipeline; replace with a simple, custom pass runner.
- GraphIR entities stay "boring": stable IDs + structure only; no provenance on ops.

Metadata system (external registries):
- Provenance/annotations live in registries keyed by GraphId.
- Pattern metadata stored as:
  - PatternExpressionRegistry: expr_id -> parsed pattern expression.
  - PatternOriginIndex: entity_id -> (expr_id, segment_index, atom_index).
  - ParamPatternOriginIndex: (inst_id, param_name) -> (expr_id, atom_index).
  - SourceSpanIndex: entity_id -> source span.
- Avoid per-atom storage of base_name/pattern_parts on graph nodes.

Lowering and pattern modularity:
- AST->GraphIR should be a staged pipeline: resolve symbols -> parse pattern table ->
  build GraphSeed (pattern refs, no expansion) -> bind/expand plan -> materialize GraphIR.
- Pattern logic lives in a dedicated pattern service (parse/validate/bind/expand),
  with stateless verifiers and clear inputs/outputs.

API vs CLI boundaries:
- CLI is a thin wrapper over a programmatic API.
- API should expose: parse/load, build_graph, verify, pattern tooling,
  design queries, and emission (no CLI-only globals).
- Diagnostics are always returned as data, not raised.

Schematic / visualization:
- Schematic should consume non-atomized views (PatternedGraph/GraphSeed or
  coalesced view derived from registries).
- Schematic will not support zoomable expansion for now.

Endpoints list-of-lists (authoring + schematic hints):
- Allow `endpoints` as list-of-lists for authoring convenience and visualization hints.
- Semantics unchanged: flatten deterministically for GraphIR (outer order, then inner).
- Record group boundaries in a schematic hints registry keyed by net_id.
- UI renders groups as net nodes, star-connected via the first group as hub.

Named pattern axes / broadcast (in new architecture):
- Axis metadata and binding rules live in the pattern service + registries only.
- GraphIR/PatternedGraph nodes carry only expr_id references, no axis info.
- Named-axis broadcast matches by axis_id; shared axes must match sizes, missing
  axes broadcast (subsequence rule for axis order).

PatternedGraph structure (no atomized nodes):
- NetBundle: net_id, name_expr_id, endpoint_ids.
- EndpointBundle: endpoint_id, net_id, port_expr_id (no inst_id; may expand to
  multiple instances).
- InstanceBundle: inst_id, name_expr_id, ref_sym, param_expr_ids.
- Pattern registry stores segments/axes; binding plans map net expr to endpoint expr.
