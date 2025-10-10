## Circuit Tree & CRef Design Decisions (First Cut)

### Scope and Goals

- **cref system**: Stable, hierarchical canonical references for voltages, currents, and operating-point scalars.
- **aliasing**: Represent net equivalence across hierarchy without flattening; enable hard-linked storage in results.
- **design tree**: Treat elaborated instance tree as a first-class artifact for tools (sim, viz, layout, analysis).
- **agent/REPL**: Provide ergonomic, discoverable navigation and signal selection without simulator coupling.

---

### Canonical Reference (cref) Syntax

- **Form**: Dot-separated, rooted at `top`.
  - Voltage: `top.amp.m1.d.v`
  - Current: `top.amp.m1.d.i`
  - OP param: `top.amp.m1.op.gm`
- **Rationale**: Human-readable, easy to tokenize, maps 1:1 to HDF5 group paths, REPL-friendly.
- **Policy**: Persist pure dot paths. Provide REPL sugar like `.v("d")`, `.i("s")`, `.op("gm")` only at the API layer.

---

### Alias Model (Net Equivalence Sets)

- **Artifact**: `net_cref_sets.json` capturing equivalence classes of crefs that represent the same physical net/quantity.
- **Structure** (conceptual): `{ cref: [alias1, alias2, ...] }` where each list is one set; choose representative deterministically (lexicographic min).
- **HDF5 storage**: Store one dataset per set and create hard links for aliases so all crefs resolve to the same data.
- **Why not flat maps**: Sets reflect symmetry and bidirectionality; avoid canonical redirect churn and keep browsing intuitive.

---

### Design Tree Artifact

- **Artifact**: `design_tree.json` emitted post-elaboration (imports resolved, patterns expanded, env vars resolved).
- **Per-node fields**:
  - `path`: instance path like `top.bias.mn1`
  - `model`: referenced module name
  - `ports`: resolved pin→net map at that scope (for primitives) or declared interface ports for subcircuits
  - `params`: merged effective parameters for this instance
  - `children`: dict of child nodes (for hierarchical modules)
  - Optional: `nets` (interface nets), `internal_nets` (locals), `metadata`
- **Naming**: Use elaborated, post-expansion names to ensure stability and alignment with generator output.

Example node:

```json
{
  "path": "top.bias.mn1",
  "model": "nmos",
  "ports": { "d": "ibias", "g": "vref", "s": "vss", "b": "vss" },
  "params": { "w": 3e-6, "l": 0.28e-6 },
  "children": {}
}
```

---

### CLI Additions

- **`asdlc design-tree`**
  - Input: ASDL file; options: `--top`, `-o design_tree.json`
  - Behavior: run `Elaborator.elaborate_with_imports(...)`, serialize tree as above.

- **`asdlc cref-aliases`**
  - Input: ASDL file; options: `--top`, `-o net_cref_sets.json`
  - Behavior: run same elaboration; traverse hierarchy and build equivalence sets from module ports and instance `mappings`.

Notes:
- Keep `asdlc visualize` as a module-scoped export for schematics; it’s orthogonal and already implemented.

---

### Results Storage (HDF5/xarray)

- **Pathing**: `/runs/<run_id>/vectors/<cref>/data` for primary datasets. Create hard links for alias crefs to the same dataset.
- **Metadata**: Dataset attrs include `{ unit, source_vec, node_kind, aliases, canonical_cref }`.
- **Companions**: Store `probe_map.json` (cref ↔ simulator vector) and copy inputs (`netlist`, `params.yaml`, `design_tree.json`, `net_cref_sets.json`).
- **Why**: Stable crefs decouple results from simulator naming and keep datasets portable.

---

### REPL / Agent API

- **Navigation**: Dot-walkable hierarchy with tab completion.
- **Convenience**: `.v/.i/.op` return cref proxies; binding to simulator vectors is adapter work.
- **Introspection**: `.describe()`, `.list_children()`, `.to_dict()` for safe prompting and discovery.
- **CRef generation**: API returns canonical dot-paths for persistence and cross-tool handoff.

---

### Integration with Current ASDL

- **Elaboration**: Use `Elaborator.elaborate_with_imports(...)` as the only source for the design tree to ensure imports, patterns, and env vars are resolved.
- **Data structures**: `Module`, `Instance`, `Port` already model unified primitives and hierarchy; leverage these for tree emission.
- **Visualization**: Keep graph exports under `prototype/visualizer_react_flow` with the existing `{asdl_basename}.{module}.sch.json` convention.

---

### Risks & Pitfalls

- **Pattern expansion drift**: Never build names from raw parse; rely on elaborated structures.
- **Namespace collisions**: Distinguish interface nets (ports) from `internal_nets`; only alias across scopes via explicit `mappings`/ports.
- **Top overrides**: Thread `--top` consistently through elaboration and all artifact emissions.
- **Determinism**: Use stable ordering and representative selection to minimize diff noise between runs.

---

### Decisions (MVP)

- **Persisted cref syntax**: Dot-separated paths rooted at `top`.
- **Alias representation**: Equivalence sets with HDF5 hard links per alias cref.
- **Design tree**: Emit post-elaboration as a standalone artifact consumed by sim, viz, and analysis tools.
- **Adapter boundary**: Simulator name binding resides in adapters; persisted IDs remain crefs.

---

### Open Questions

- Do we expose a separate `/nets/<name>` browsing namespace in HDF5, or only per-cref paths plus links?
- How should we surface device-level OP groups vs node-level waveforms in the REPL API (namespacing and discoverability)?
- What minimal schema/versioning do we embed in `design_tree.json` and `net_cref_sets.json` for forward compatibility?

---

### Immediate Next Steps

1) Implement `asdlc design-tree` and `asdlc cref-aliases` using the elaborated ASDL model.
2) Add unit tests on small examples (e.g., inverter, diff pair) to assert crefs and alias sets.
3) Draft thin Python wrappers for REPL navigation (`tree`, `modules`) returning crefs and proxies.
4) When implementing the ngspice shared runtime, adopt the hard-link strategy and keep crefs first-class.


