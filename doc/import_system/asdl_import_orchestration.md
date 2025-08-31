# ASDL Import Orchestration — Design & Example

This document captures the orchestration flow for the unified import strategy in ASDL, plus the design decisions, rationales, and a complete toy example from multi-file sources → elaborated single-file ASDL → SPICE netlist (hierarchical and fully flat).

---

## Goals

- Keep **parsing** purely about syntax/shape; avoid IO at parse time.
- Perform **import resolution** during **elaboration Phase 0**, before pattern expansion and variable/parameter resolution.
- Produce a **single-file ASDL compilation unit** (imports removed, reachable modules hoisted) that is deterministic, easy to diff, and ready for downstream passes and netlisting.
- Provide clear **diagnostics** (missing files, circular imports, alias collisions, unknown modules).

---

## Orchestration Flow (Phases)

### Phase 0 — Import Resolution (new)
1. **Build search paths** in priority: CLI → config → `ASDL_PATH` → defaults (`./`, `libs/`, `third_party/`).
2. **Resolve imports recursively (DFS):**
   - Resolve each `imports: {alias: "relative/path.asdl"}` to an absolute path by probing search paths (first match wins).
   - Maintain a `loading_stack` for **circular dependency** detection and a `cache` of `{abs_path: ASDLFile}` for reuse.
   - Parse each imported file and recurse on its imports until the **dependency DAG** is discovered.
3. **Validate model aliases:** format, collisions with import names, unknown import alias, unknown module within an import.
4. **Build module tables & bind references:** enable three-step lookup (local → `model_alias` → qualified `import_alias.module`).
5. **Hoist reachable modules** into the main compilation unit; **drop `imports`**; optionally **prune unreachable** modules (only keep modules reachable from the chosen top module).

**Traversal Choice:** Depth‑First Search (DFS) for loading makes cycle detection and “ready when children done” semantics natural; use a topological order later when applying deterministic downstream passes.

### Phase 1 — Pattern Expansion
- Expand literal name patterns (`<>`) and bus patterns (`[N:M]`) for **ports**, **instance IDs**, and **mapping keys**.
- Expand **mapping patterns** once instances are expanded.

### Phase 2 — Variable/Parameter Resolution
- Resolve variables/parameters used in instance parameters against module variables.

### Output — Netlisting
- Emit **hierarchical** SPICE (preferred for debug) or **fully flattened** SPICE (optional) by inlining hierarchy post‑order.

---

## Key Design Decisions & Rationale

- **Resolve imports during elaboration, not parsing.**  
  *Rationale:* keeps parser deterministic, side‑effect free and testable; filesystem/search‑path concerns live in the orchestrator; enables caching and cycle handling.

- **Unified module table with local preference.**  
  *Rationale:* authors can override or wrap imported functionality locally; explicit qualifiers (`import_alias.module`) remain available to disambiguate.

- **Strict alias format (`import_alias.module`).**  
  *Rationale:* removes ambiguity; easy to statically validate and to qualify/rename later.

- **Environment‑aware search paths in stable priority order.**  
  *Rationale:* reproducible builds across machines; explicit, inspectable probing lists for better diagnostics.

- **Single-file “flat ASDL” as the elaboration product.**  
  *Rationale:* reliable artifact for review, caching and netlisting; tooling doesn’t have to keep chasing imports after elaboration.

---

## Toy Example

### Project Layout

```
.
├── libs/
│   ├── primitives.asdl
│   └── opamp.asdl
└── top.asdl
```

### `libs/primitives.asdl`

```yaml
file_info:
  name: primitives

modules:
  nfet_03v3:
    device_line: "M @D @G @S @B nfet_03v3 L=0.28u W=3u"
  pfet_03v3:
    device_line: "M @D @G @S @B pfet_03v3 L=0.28u W=6u"
```

### `libs/opamp.asdl`

```yaml
file_info:
  name: opamp

imports:
  prim: primitives.asdl

model_alias:
  nmos: prim.nfet_03v3
  pmos: prim.pfet_03v3

modules:
  ota_diffpair:
    ports: [in_p, in_n, out, vdd, vss]
    instances:
      MN1: {model: nmos, D: out, G: in_p, S: vss, B: vss}
      MN2: {model: nmos, D: out, G: in_n, S: vss, B: vss}
      MP1: {model: pmos, D: out, G: in_p, S: vdd, B: vdd}
```

### `top.asdl`

```yaml
file_info:
  name: top

imports:
  op: libs/opamp.asdl

modules:
  top_amp:
    ports: [in_p, in_n, vdd, vss, out]
    instances:
      A1: {model: op.ota_diffpair, in_p: in_p, in_n: in_n, vdd: vdd, vss: vss, out: out}
```

---

## Elaboration Result — Single‑File ASDL (imports removed)

```yaml
file_info:
  name: top_flat

modules:
  nfet_03v3:
    device_line: "M @D @G @S @B nfet_03v3 L=0.28u W=3u"

  pfet_03v3:
    device_line: "M @D @G @S @B pfet_03v3 L=0.28u W=6u"

  ota_diffpair:
    ports: [in_p, in_n, out, vdd, vss]
    instances:
      MN1: {model: nfet_03v3, D: out, G: in_p, S: vss, B: vss}
      MN2: {model: nfet_03v3, D: out, G: in_n, S: vss, B: vss}
      MP1: {model: pfet_03v3, D: out, G: in_p, S: vdd, B: vdd}

  top_amp:
    ports: [in_p, in_n, vdd, vss, out]
    instances:
      A1: {model: ota_diffpair, in_p: in_p, in_n: in_n, vdd: vdd, vss: vss, out: out}
```

Notes:
- `imports:` and `model_alias:` are gone.
- Instance `model:` values are bound to modules present in this single file.

---

## Netlist Generation

### Option A — Hierarchical SPICE (subcircuits preserved)

```spice
* ===== Primitive model cards (PDK) =====
* .include/.model lines go here (referenced by device_line names)
* .model nfet_03v3 nmos (...)
* .model pfet_03v3 pmos (...)

* ===== ota_diffpair subckt =====
.subckt ota_diffpair in_p in_n out vdd vss
M_MN1 out in_p vss vss nfet_03v3 L=0.28u W=3u
M_MN2 out in_n vss vss nfet_03v3 L=0.28u W=3u
M_MP1 out in_p vdd vdd pfet_03v3 L=0.28u W=6u
.ends ota_diffpair

* ===== top_amp =====
.subckt top_amp in_p in_n vdd vss out
X_A1 in_p in_n out vdd vss ota_diffpair
.ends top_amp
```

### Option B — Fully Flattened SPICE (inline hierarchy)

```spice
* Primitive model cards as above…

.subckt top_amp in_p in_n vdd vss out
M_A1__MN1 out in_p vss vss nfet_03v3 L=0.28u W=3u
M_A1__MN2 out in_n vss vss nfet_03v3 L=0.28u W=3u
M_A1__MP1 out in_p vdd vdd pfet_03v3 L=0.28u W=6u
.ends top_amp
```

**Name scoping:** inline devices are prefixed with the parent instance path (e.g. `A1__MN1`) to ensure uniqueness and traceability.

---

## Orchestrator Skeleton (Illustrative)

```python
def elaborate_with_imports(main_file_path, cli_paths=None, config_paths=None):
    # Phase 0: imports
    search = PathResolver().get_search_paths(cli_paths, config_paths)
    cache, diags = load_dependency_dag(main_file_path, search)  # DFS + cycle detection
    main = cache[Path(main_file_path).resolve()]

    diags += AliasResolver().validate_model_aliases(main, cache)
    bind_models_inplace(main, cache)  # uses ModuleResolver

    flat = hoist_reachable_modules(main, cache)  # prune, drop imports

    # Phase 1: pattern expansion
    flat, d1 = PatternExpander().run(flat); diags += d1

    # Phase 2: variable/param resolution
    flat, d2 = VariableResolver().run(flat); diags += d2

    return flat, diags
```

That’s the whole flow: parse → **import resolve** (DFS) → expand patterns → resolve variables → netlist.
