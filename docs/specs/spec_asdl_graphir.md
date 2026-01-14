# ASDL GraphIR (xDSL Dialect) Specification

Status: Draft

## 1. Purpose and Scope

GraphIR is the canonical semantic representation of ASDL designs. It is the
single source of truth for connectivity, refactor operations, and structural
verification. IFIR is the emission projection, and NFIR is an optional
authoring/roundtrip projection derived from GraphIR.

GraphIR is defined as an xDSL dialect to reuse the existing pass infrastructure
and diagnostics system while enforcing hypergraph semantics.

Pipeline placement:
AST -> GraphIR (verify) -> IFIR -> emission. Pattern expansion metadata and
atomization are part of GraphIR construction. GraphIR is the canonical semantic
core in this flow; NFIR is optional and not part of the critical path.

## 2. Design Goals

- Semantic clarity: all structural correctness checks live in GraphIR.
- Refactorability: edits are expressed as primitive graph operations.
- Determinism: stable IDs and deterministic serialization.
- Pattern preservation: rebundle atomized patterns without inference.

## 3. Program Model

GraphIR models a program as a set of module graphs and device symbols with
explicit dependencies. Each module graph is a hypergraph of instances and nets.

GraphIR includes a program container:
- `graphir.program` op owns module graphs and device symbols.
- `entry` is optional; `None` indicates a library-only program.
- `entry` refers to a module ID, not a device symbol.
- All modules from input files are retained (reachable or not).

Symbol references are resolved before GraphIR construction. GraphIR stores:
- `module_ref`: a resolved symbol reference (module or device).
- `module_ref_raw`: original textual reference for provenance.

Unresolved references are not permitted in GraphIR.

### 3.1 Module Ordering and Emission Scope

Library files:
- Emit all modules.
- Preserve ASDL file order; if multiple files are present, order by entry file
  first, then imports in resolution order, and preserve module order per file.

Design files:
- Emit reachable modules only (after any substitution pass).
- Use DFS post-order from `entry` so dependencies appear before use and the top
  module appears last.

Note: this derived emission order does not mutate GraphIR region ordering.

### 3.2 GraphIR Canonical Ordering

GraphIR preserves region order as canonical for stable diffs:
- `graphir.program` module order follows ASDL file order and per-file module
  order (entry file first, then imports in resolution order).
- `graphir.module` preserves net list order and instance list order as region
  order.
- `graphir.bundle` order follows expander output order.
- `graphir.module.attrs.port_order` preserves the `$`-net-derived port order
  (names stored without `$` and expanded to atoms).

Edits append by default. If a pass needs a specific placement, it must use
explicit move/insert operations; renames never reorder.

### 3.3 Emit Name Resolution and Collisions

Module identity is `(file_id, name)`. Emitted subckt names are derived during
emission:
- If two reachable modules would emit the same name, rename the colliding
  module(s) with suffix `__{hash8(file_id)}` and emit a warning listing renames.
Device symbols are emitted via backend templates and are not subject to
subckt rename rules.

## 4. Core Entities

### 4.1 Stable IDs

All entities carry stable opaque IDs (integer or UUID):
- IDs are never reused.
- Names are attributes, not identity.

### 4.2 SymbolRef

Resolved symbol references are explicit:

```
SymbolRef { kind: module | device, id: GraphId }
```

`module_ref_raw` preserves the original textual reference.

### 4.3 Instance

Represents a module or device instantiation.

```
Instance {
  id: InstID
  name: str
  module_ref: SymbolRef        # resolved module/device reference
  module_ref_raw: str          # provenance
  props: dict[str, Value]
  annotations: dict
}
```

### 4.4 Net

Represents a connectivity object (hyperedge).

```
Net {
  id: NetID
  name: str
  attrs: dict
  annotations: dict
}
```

### 4.5 Endpoint

Represents a concrete attachment point.

```
Endpoint {
  id: EndpointID
  inst_id: InstID
  port_path: str
}
```

Unique key: `(inst_id, port_path)`; `id` is a stable opaque identifier.
Port paths are single-segment strings; `.` is reserved for endpoint expressions
(`inst.port`) and is forbidden in port names. Hierarchical paths are deferred.

### 4.6 ParamRef

Represents a specific instance parameter for pattern ownership.

```
ParamRef {
  inst_id: InstID
  param_name: str
}
```

### 4.7 Device

Represents a leaf symbol with ports and backend metadata.

```
Device {
  id: DeviceID
  name: str
  file_id: str
  ports: list[str]
  params: dict[str, Value]
  backends: list[BackendSpec]
  annotations: dict
}
```

## 5. Incidence Model (Derived Indices)

GraphIR canonical storage is `graphir.endpoint` ops nested under `graphir.net`.
Incidence maps are derived indices:

```
net_to_endpoints: dict[NetID, list[Endpoint]]
endpoint_to_net: dict[Endpoint, NetID]
inst_to_endpoints: dict[InstID, list[Endpoint]]
```

Notes:
- Lists are ordered where a stable order exists (for pattern rebundling).
- Derived indices may be cached but are not canonical.

Invariants:
- Each endpoint belongs to exactly one net.
- All endpoints reference valid instances.
- All nets and instances exist.
- Empty nets are allowed only transiently in transactions.

## 6. GraphIR Dialect Shape (xDSL)

GraphIR is implemented as a dialect under `src/asdl/ir/` with:
- `graphir.module` op containing nets, instances, endpoints, and bundles.
- `graphir.device` op for leaf symbols (ports and backend metadata only).
- `graphir.net` op with stable `net_id`, `name`, `attrs`.
- `graphir.instance` op with stable `inst_id`, `name`, `module_ref`.
- `graphir.endpoint` op with stable `endpoint_id`, `inst_id`, `port_path`.
- `graphir.bundle` op for pattern bundles (see Section 7).
- `graphir.pattern_expr` op for ordered bundle expressions with explicit owners.

Endpoints are stored as explicit ops nested under `graphir.net` regions, using
region order to define endpoint order. Reverse indices are derived.

### 6.1 Dialect Schema

See `docs/specs/spec_asdl_graphir_schema.md` for the full dialect schema.

## 7. Patterns and Bundles

Pattern expansion produces atomized tokens with metadata. GraphIR preserves
pattern information through explicit bundle metadata; no pattern inference is
allowed.

### 7.1 Bundle Metadata

```
Bundle {
  id: BundleID
  kind: net | endpoint | param | inst
  base_name: str
  pattern_type: literal | numeric
  members: list[MemberID]      # ordered
  annotations: dict
}
```

Rules:
- Bundles are created only by the pattern expander.
- `members` order is the expander output order; never sort.
- Bundle IDs are stable within GraphIR.
- A bundle represents a single contiguous segment of eligible atoms. Pattern
  expressions are ordered lists of bundles concatenated with `;`.

### 7.2 Bundle ID Stability

- Deterministic on import: derive bundle IDs from a stable key
  (module ID + pattern token + source span or NFIR op ID).
- Fracture: retain the original bundle ID for the fragment containing the
  first member in order; mint new bundle IDs for other fragments.
- Merge: mint a new bundle ID; optionally record origin bundle IDs.

### 7.3 Pattern Atom Metadata

Each atomized member produced by the expander must carry:
- `base_name`
- `pattern_type` (`literal` or `numeric`)
- `pattern_token` (string or int)
- `pattern_eligible` (true only for expander output)

### 7.4 Pattern Expressions

Pattern expressions represent the original `;`-spliced structure.

```
PatternExpr {
  id: PatternExprID
  kind: net | endpoint | param | inst
  owner: NetID | EndpointID | InstID | ParamRef
  bundles: list[BundleID]      # ordered
  annotations: dict
}
```

Rules:
- Pattern expressions are created only by the pattern expander.
- `bundles` preserves the written order; `;` boundaries are preserved.
- Each bundle belongs to at most one pattern expression of the same kind.
- `owner` kind must match `kind`.
- Binding uses flattened atom lists; expression boundaries need not align.
Bundle op order is non-semantic; only `pattern_expr.bundles` encodes order and
`;` boundaries.

### 7.5 Rebundling Rules

Rebundling is deterministic and never infers patterns.

Input: an ordered member list.

Process:
- Walk the list in order; never sort.
- Greedy-group consecutive eligible atoms with the same `base_name` and
  `pattern_type`.
- Fracture when `base_name` changes, `pattern_type` changes, or a non-eligible
  atom appears.
- Rebundling does not merge across pattern expression boundaries.

Numeric bundles:
- Require contiguous indices in the existing order (step +1 or -1).
- Split into maximal contiguous runs.
- Emit `[hi:lo]` for descending runs and `[lo:hi]` for ascending runs.

Literal bundles:
- Emit `base<suffix1|suffix2|...>` in list order.

Mixed segments:
- Concatenate rebundled segments with `;` in list order.

Example:
- `net[7:0]` with `net[4]` removed emits `net[7:5];net[3:0]`.

### 7.6 Order Preservation

Binding and rebundling use the expander order. If two patterns expand with
different orders (e.g., `net[7:0]` and `endpoint[0:7]`), their orders are
preserved independently. Rebundling never flips order.

## 8. Primitive Operations

Primitive ops form the edit algebra:

```
create_instance(module_ref, name?, props?) -> InstID
delete_instance(inst_id)
create_net(name?, attrs?) -> NetID
delete_net(net_id)
attach(net_id, endpoint)
detach(endpoint)
set_instance_prop(inst_id, key, value)
set_net_attr(net_id, key, value)
rename_instance(inst_id, new_name)
rename_net(net_id, new_name)
```

Compound edits (merge/split/rewire/clone) decompose into primitives.

## 9. Transactions and Validation

All GraphIR edits occur in transactions with commit-time validation.

Validation rules:
- No dangling endpoints.
- Endpoint uniqueness.
- Net existence.
- Instance existence.

## 10. Patches and Provenance

```
Patch {
  ops: list[PrimitiveOp]
  provenance: dict
}
```

Patches are replayable and diffable. Provenance may include intent labels and
origin bundle IDs.

## 11. Projections and Round-Trip

- GraphIR -> IFIR: normalization and backend-focused lowering.
- GraphIR -> NFIR (optional): authoring/roundtrip projection; not required for
  emission.

Round-trip goal:
- Preserve semantics and pattern structure when bundle metadata remains valid.
- Formatting/whitespace is not preserved.

No pattern inference is permitted during emission.

---

## Open questions

None.
