## Netlist IR (Minimal) — Subcircuits, Instances, Parameters

Goal: Define a simulator-agnostic IR sufficient to represent hierarchical subcircuits, instances (of primitives or subcircuits), and parameters. Leave analyses/controls/statistics for later.

### Dialect: `netlist`

- Operation: `netlist.module` (subckt)
  - attrs:
    - `sym_name: StringAttr` — subckt name
    - `ports: ArrayAttr<StringAttr>` — ordered ports (preserve declaration order)
    - `parameters: DictionaryAttr` — default parameters (values may be literals or `asdl.expr`)
  - region: single block containing instances

- Operation: `netlist.instance`
  - attrs:
    - `sym_name: StringAttr` — instance identifier
    - `model_ref: StringAttr` — referenced primitive/subckt name
    - `pin_map: DictionaryAttr` — mapping `portName -> netName` (named connectivity preserved)
    - `pin_order: ArrayAttr<StringAttr>` — callee port order for positional backends
    - `parameters: DictionaryAttr` — parameter overrides (values may be literals or `asdl.expr`)
  - operands: none (Phase 0). SSA wires may be introduced later with `netlist.net`.

### Attributes
- Reuse `asdl.ExprAttr` for parameter values that are expressions.
- Use builtin `StringAttr`, `ArrayAttr`, `DictionaryAttr` for structure.

### Lowering (ASDL → netlist)
- Module: map name, preserve port order, copy parameters if present.
- Instance: map id, model, parameters; build `pin_map` from ASDL mappings; compute `pin_order` from callee module’s declared ports.
- No explicit net ops in this phase; net names are strings referenced by `pin_map`.

### Textual printing (golden-friendly)
```
netlist.module @<name> ports=["p","n"] params={...} {
  netlist.instance @<id> model="<model>" pin_map={p:"net_p", n:"0"} pin_order=["p","n"] params={}
}
```
- Preserve port order; sort dictionary keys for stable diffs.

### Textual netlist emitter (development)
- Module path: `src/asdl/ir/netlist_text.py`
- Entry: `emit_netlist_text(builtin_module, dialect={ngspice|neutral})`
- CLI: `asdlc ir-dump --engine xdsl --lower netlist-text --sim {ngspice|neutral} file.asdl`
- Dialects:
  - `ngspice`: `.subckt <name> <ports...>` and positional pins on `X<id>`, `.ends`
  - `neutral`: same `.subckt/.ends` but named pins `pin=net` to aid debugging

### Out-of-scope (future)
- `netlist.net` SSA wires, explicit net declarations
- Analyses/controls/options, includes/models, stats/corners
- Verifiers: uniqueness, pin count/name checks

### Tests
- Fixtures: primitive with ordered ports; single-inst top mapping ports to nets.
- Assertions: port order preserved, `pin_map` correct, `pin_order` matches callee ports, deterministic printer.


