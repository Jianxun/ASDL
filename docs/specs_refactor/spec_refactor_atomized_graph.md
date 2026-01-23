# Refactor Spec - AtomizedGraph Core Model

Status: Draft (refactor-only; not canonical)

## 1. Purpose
Define the AtomizedGraph core model as a fully-expanded, pattern-free view of a
program. AtomizedGraph is derived from PatternedGraph and is intended for
verification and emission adapters that require literal net/instance/endpoint
names.

## 2. Design Goals
- Store only fully-resolved (atomized) names; no pattern expressions remain.
- Preserve stable IDs for deterministic cross-referencing.
- Allow optional provenance links back to PatternedGraph entities.
- Keep structure minimal and deterministic for emission and validation.

## 3. Program Model
AtomizedGraph mirrors the PatternedGraph shape but with literal names and
atomized endpoints.

```
AtomizedProgramGraph {
  modules: dict[AtomizedModuleId, AtomizedModuleGraph]
}

AtomizedModuleGraph {
  module_id: GraphId
  name: str
  file_id: str
  port_order: list[str] | None
  nets: dict[AtomizedNetId, AtomizedNet]
  instances: dict[AtomizedInstId, AtomizedInstance]
  endpoints: dict[AtomizedEndpointId, AtomizedEndpoint]
  patterned_module_id: GraphId | None
}
```

### 3.1 AtomizedNet
```
AtomizedNet {
  net_id: GraphId
  name: str
  endpoint_ids: list[AtomizedEndpointId]
  patterned_net_id: GraphId | None
  attrs: dict | None
}
```

### 3.2 AtomizedInstance
```
AtomizedInstance {
  inst_id: GraphId
  name: str
  ref_kind: "module" | "device"
  ref_id: GraphId
  ref_raw: str
  param_values: dict[str, object] | None
  patterned_inst_id: GraphId | None
  attrs: dict | None
}
```

### 3.3 AtomizedEndpoint
```
AtomizedEndpoint {
  endpoint_id: GraphId
  net_id: GraphId
  inst_id: GraphId
  port: str
  patterned_endpoint_id: GraphId | None
  attrs: dict | None
}
```

## 4. Provenance
Provenance fields (`patterned_*_id`) are optional back-references to the
originating PatternedGraph entities. They enable traceability without
reintroducing pattern expressions into the atomized view.

## 5. Invariants
- Atomized names must not contain pattern delimiters (`<`, `>`, `;`).
- Endpoint atoms must reference existing nets and instances.
- Each endpoint belongs to exactly one net.
- Net names must be unique within a module.
- Instance names must be unique within a module.
- Each instance port binds to exactly one net.
- Each net must have at least one endpoint.
- `port_order`, when present, lists only literal port names.
- Provenance references may be absent; consumers must tolerate missing data.
