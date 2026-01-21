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
  registries: RegistrySet
}

ModuleGraph {
  module_id: GraphId
  name: str
  file_id: str
  port_order: list[str] | None
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
  annotations: dict | None
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
  annotations: dict | None
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
  annotations: dict | None
}
```

## 4. Registries
Registries hold metadata keyed by IDs; they are not stored on the graph nodes.

```
RegistrySet {
  pattern_expressions: PatternExpressionRegistry
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
- Registry data is optional; tools must tolerate missing registries.

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

## 7. Compatibility
PatternedGraph is the primary API model. Atomized GraphIR (legacy or emission)
is a derived view produced by applying the pattern service and expansion plans.
