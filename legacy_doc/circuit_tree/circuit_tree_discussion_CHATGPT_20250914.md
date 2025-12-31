# ✅ ASDL + Simorc Cref & Design Tree System — Summary (2025‑09‑14)

## 🔧 Goals

- Build a **canonical reference system (cref)** for voltage, current, and operating point access.
- Resolve **hierarchical aliases** so multiple crefs that point to the same physical net are **hard-linked** in HDF5.
- Enable **agentic and REPL-style access** to simulation results and circuit structure.
- Treat the **design tree** and **ASDL module definitions** as first-class artifacts for downstream tools.

---

## 📘 Cref Types & Syntax (MVP)

| Type         | Syntax Example            | HDF5 Path                  |
|--------------|---------------------------|----------------------------|
| Voltage      | `top.amp.m1.d.v`          | `/top/amp/m1/d/v`          |
| Current      | `top.amp.m1.d.i`          | `/top/amp/m1/d/i`          |
| DC OP Param  | `top.amp.m1.op.gm`        | `/top/amp/m1/op/gm`        |

✅ Dot-separated `cref` syntax is:
- Human-readable
- Tokenizable by REPL/agent
- Mappable to HDF5 groups
- Preferred over `v("d")` or `i("s")` function-call forms

---

## 🔁 Cref Aliasing via `net_cref_sets`

Instead of flattening to `cref → canonical`, define:

```json
{
  "top.vref": [
    "top.bias.mn1.d",
    "top.amp.vref_in",
    "top.amp.m2.s"
  ]
}
```

→ This defines **equivalence sets**. During post-processing:
- Store vector once (under `/nets/top/vref`)
- Create **HDF5 hard links** for all aliases (e.g., `top.amp.m2.s.v`)

---

## 🌳 Design Tree (Elaborated Instance Tree)

Design tree is a **structural elaboration** of the top-level ASDL module.

Example structure (`design_tree.json`):

```json
{
  "path": "top.bias.mn1",
  "type": "n_mos_tile",
  "ports": { "d": "ibias", "g": "vref", "s": "vss" },
  "params": { "w": 3e-6, "l": 0.28e-6 },
  "children": {}
}
```

- Should be emitted via `asdlc --emit-design-tree`
- Used for:
  - cref resolution
  - schematic visualization
  - layout group analysis
  - symbolic modeling

---

## 🧭 Navigating the Design Tree in REPL

Python REPL-style access:

```python
tree.top.bias.mn1.ports     # → {'d': 'ibias', 'g': 'vref', 's': 'vss'}
tree.top.bias.mn1.path      # → 'top.bias.mn1'
tree.top.bias.children      # → {'mn1': ...}
tree.top.bias.nets          # → ['vref', 'ibias']
```

Design tree nodes should support:

- `__getattr__()` → for navigation
- `__dir__()` → for tab completion
- `.describe()` → summary metadata
- `.to_dict()` → JSON serialization

---

## 📚 ASDL Module Definitions

Separate from the design tree, `modules:` define **parametric, reusable templates**.

REPL-style access:

```python
modules.ota.ports           # {'vin': 'vin', 'vout': 'vout'}
modules.ota.children        # {'mn_in': 'n_mos_tile', ...}
modules.ota.metadata        # layout hints, grouping
```

Expose:
- `modules.<modname>`
- `.ports`, `.children`, `.params`, `.metadata`
- Optional: `.describe()`, `.to_yaml()`

---

## 🧠 Agent Introspection & Execution

### What the agent can do:
- Traverse hierarchy via dot access
- Discover structure via `dir()` or `.list_children()`
- Inspect devices, ports, nets, parameters
- Generate valid crefs for simulation
- Use `.v`, `.i`, `.op.gm` to query signals
- Normalize cref aliases via `alias_table` or `net_cref_sets`

### REPL design requirements:
| Feature           | Purpose                      |
|------------------|------------------------------|
| `__getattr__`     | dot-based navigation         |
| `__dir__`         | tab completion               |
| `.describe()`     | summarize node/module        |
| `.list_children()`| introspection                |
| `.to_dict()`      | for LLM agent prompt injection |
| `.resolve_cref()` | cref to canonical net        |

### Modes of interaction:
- Python REPL / Jupyter (agent runs code)
- CLI REPL (agent calls subprocess)
- Tool calling / OpenAPI (agent uses function registry)

---

## 🗂️ Final Artifact Summary

| File | Purpose |
|------|---------|
| `design_tree.json`     | Elaborated structure |
| `net_cref_sets.json`   | Cref → net aliases   |
| `cref_alias_table.json`| Optional flat cref map |
| `modules.json`         | Parsed ASDL module defs |
| `results.h5`           | Simulation results   |

---

## 🧰 Next Steps (Implementation)

- [ ] Emit `design_tree.json` from `asdlc`
- [ ] Emit `net_cref_sets.json` for alias resolution
- [ ] Create Python REPL interfaces:
  - `tree`
  - `sim`
  - `modules`
- [ ] Add `.describe()`, `.to_dict()`, `.resolve_cref()` helpers
- [ ] Enable REPL as both human/agent interface

