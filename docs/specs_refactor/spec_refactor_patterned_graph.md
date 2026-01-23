# Refactor Spec - PatternedGraph Core Model

Status: Draft (refactor-only; not canonical)

## 1. Purpose
Define the new PatternedGraph core model that preserves authored pattern
expressions while keeping the graph structure minimal. PatternedGraph is the
programmatic API surface for design queries and visualization. Atomized graphs
are derived artifacts for emission and legacy compatibility.

## 2. Design Goals
- Keep the graph "boring": stable IDs + structure only, no pattern metadata.
- Preserve authored pattern expressions via registry references (expr_id).
- Enable schematic visualization without atomized expansion.
- Support deterministic traversal and query APIs.

## 3. Program Model
PatternedGraph is a program of modules. Each module contains nets, instances,
and endpoints. Nets own endpoint bundles (hyperedges).

```
ProgramGraph {
  modules: dict[ModuleId, ModuleGraph]
  devices: dict[DeviceId, DeviceDef]
  registries: RegistrySet
}

ModuleGraph {
  module_id: GraphId
  name: str
  file_id: str
  ports: list[str]
  nets: dict[NetId, NetBundle]
  instances: dict[InstId, InstanceBundle]
  endpoints: dict[EndpointId, EndpointBundle]
}
```

### 3.1 NetBundle
```
NetBundle {
  net_id: GraphId
  name_expr_id: ExprId
  endpoint_ids: list[EndpointId]
  attrs: dict | None
}
```

### 3.2 InstanceBundle
```
InstanceBundle {
  inst_id: GraphId
  name_expr_id: ExprId
  ref_kind: "module" | "device"
  ref_id: GraphId
  ref_raw: str
  param_expr_ids: dict[str, ExprId] | None
  attrs: dict | None
}
```

### 3.3 EndpointBundle
Endpoint bundles carry the full endpoint expression (`inst.pin`) via an
expression id. They may expand to atoms that reference multiple instances.
```
EndpointBundle {
  endpoint_id: GraphId
  net_id: GraphId
  port_expr_id: ExprId
  attrs: dict | None
}
```

### 3.4 DeviceDef
Devices are leaf definitions that provide port ordering and metadata for
emission and verification. Backend templates are not stored here.
```
DeviceDef {
  device_id: GraphId
  name: str
  file_id: str
  ports: list[str]
  parameters: dict[str, object] | None
  variables: dict[str, object] | None
  attrs: dict | None
}
```

## 4. Registries
Registries hold metadata keyed by IDs; they are not stored on the graph nodes.

```
RegistrySet {
  pattern_expressions: PatternExpressionRegistry
  pattern_origins: PatternOriginIndex
  param_pattern_origins: ParamPatternOriginIndex
  source_spans: SourceSpanIndex
  schematic_hints: SchematicHints
  annotations: AnnotationIndex
}
```

### 4.1 PatternExpressionRegistry
```
PatternExpressionRegistry {
  expr_id: PatternExpr
}
```
`PatternExpr` retains parsed segments, axis metadata, and source spans. See
`spec_refactor_pattern_service.md`.

### 4.1a PatternOriginIndex
```
PatternOriginIndex {
  entity_id: (expr_id, segment_index, atom_index)
}
```

### 4.1b ParamPatternOriginIndex
```
ParamPatternOriginIndex {
  (inst_id, param_name): (expr_id, atom_index)
}
```

### 4.2 SourceSpanIndex
```
SourceSpanIndex {
  entity_id: SourceSpan
}
```

### 4.3 SchematicHints
Optional layout-only metadata. Connectivity is unaffected.
```
SchematicHints {
  net_id: [GroupSlice]
  hub_group_index: int = 0
}

GroupSlice {
  start: int
  count: int
  label: str | None
}
```
If `endpoints` is authored as a list-of-lists, the lowerer records group slices
for the flattened endpoint order.

## 5. Invariants
- Each endpoint belongs to exactly one net.
- All referenced IDs must exist in the module.
- Endpoint bundles do not store instance IDs; per-instance endpoints are derived
  by pattern expansion.
- Module and device `ports` are always lists (empty list allowed).
- Module `ports` entries are normalized names (strip leading `$` at ingest).
- Module `ports` ordering is semantic and must be preserved (never sorted).
- Registry data is optional; tools must tolerate missing registries.
- Net name expressions must not contain splices (`;`); split net entries per segment.

## 6. Query/Index Layer (Derived)
The query layer builds indices from the graph + registries. Indices are not
stored on the graph.

```
GraphIndex {
  net_to_endpoints: dict[NetId, list[EndpointId]]
  inst_name_to_id: dict[str, InstId]
  net_name_to_id: dict[str, NetId]
}
```
Per-instance endpoints require expansion via the pattern service.

## 7. JSON Serialization
PatternedGraph can be serialized via `patterned_graph_to_jsonable` and
`dump_patterned_graph`. The JSON payload mirrors the graph structure and
registries with deterministic ordering (sorted keys).

```
{
  "modules": [
    {
      "module_id": "m1",
      "name": "top",
      "file_id": "design.asdl",
      "ports": ["vdd"],
      "nets": [
        {"net_id": "n1", "name_expr_id": "expr1", "endpoint_ids": ["e1"], "attrs": null}
      ],
      "instances": [
        {
          "inst_id": "i1",
          "name_expr_id": "expr2",
          "ref_kind": "device",
          "ref_id": "dev1",
          "ref_raw": "M1",
          "param_expr_ids": {"w": "expr3"},
          "attrs": null
        }
      ],
      "endpoints": [
        {"endpoint_id": "e1", "net_id": "n1", "port_expr_id": "expr4", "attrs": null}
      ]
    }
  ],
  "devices": [
    {
      "device_id": "d1",
      "name": "nmos",
      "file_id": "design.asdl",
      "ports": ["D", "G", "S", "B"],
      "parameters": null,
      "variables": null,
      "attrs": null
    }
  ],
  "registries": {
    "pattern_expressions": {"expr1": PatternExprJson} | null,
    "pattern_origins": {
      "n1": {"expr_id": "expr1", "segment_index": 0, "token_index": 0}
    } | null,
    "param_pattern_origins": [
      {"inst_id": "i1", "param_name": "w", "expr_id": "expr1", "token_index": 0}
    ] | null,
    "source_spans": {"n1": SourceSpanJson} | null,
    "schematic_hints": {
      "net_groups": {"n1": [{"start": 0, "count": 1, "label": "bus"}]},
      "hub_group_index": 0
    } | null,
    "annotations": {"n1": {"role": "signal"}} | null
  }
}
```

`PatternExprJson` mirrors the pattern service data:
```
PatternExprJson {
  "raw": "N<1|2>",
  "segments": [
    {
      "tokens": [
        {"kind": "literal", "text": "N", "span": SourceSpanJson},
        {
          "kind": "group",
          "group_kind": "enum",
          "labels": [1, 2],
          "axis_id": "n",
          "span": SourceSpanJson
        }
      ],
      "span": SourceSpanJson
    }
  ],
  "axes": [
    {"axis_id": "n", "kind": "enum", "labels": [1, 2], "size": 2, "order": 0}
  ],
  "axis_order": ["n"],
  "span": SourceSpanJson
}
```

`SourceSpanJson` uses the diagnostics span schema:
```
SourceSpanJson {
  "file": "design.asdl",
  "start": {"line": 1, "col": 1},
  "end": {"line": 1, "col": 6},
  "byte_start": 0,
  "byte_end": 5
}
```

## 8. Compatibility
PatternedGraph is the primary API model. Atomized GraphIR (legacy or emission)
is a derived view produced by applying the pattern service and expansion plans.
