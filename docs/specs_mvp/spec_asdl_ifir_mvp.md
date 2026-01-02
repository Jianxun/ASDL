# Spec - ASDL_IFIR (Instance-First IR) v0 (MVP)

## Purpose
ASDL_IFIR is an instance-first, netlist-oriented IR with explicit nets and
named-only connections. It is the final pre-emission representation in the MVP
pipeline.

---

## MVP scope
- Self-contained design (no imports/exports/includes).
- No pattern domains or wildcards; names are explicit.
- Named-only connections (no positional conns).
- Explicit net objects are declared in each module.
- No view system and no device kind inference.
- Multiple backend templates may remain attached to devices.

---

## Draft ops (xDSL dialect `asdl_ifir`)

### `asdl_ifir.design`
**Role**: top-level container.

**Attributes**
- `top: StringAttr?`
  - Entry module name (from AST `top`).
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_ifir.module*`, `asdl_ifir.device*`

### `asdl_ifir.module` (symbol)
**Attributes**
- `sym_name: StringAttr`
- `port_order: ArrayAttr<StringAttr>`
  - Ordered list of port names derived from `$` nets in AST.
  - Port names are stored without the `$` prefix.
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_ifir.net*`, `asdl_ifir.instance*`

### `asdl_ifir.net`
**Attributes**
- `name: StringAttr`
- `net_type: StringAttr?`
- `src: LocAttr?`

### `asdl_ifir.instance`
**Attributes**
- `name: StringAttr`
- `ref: SymbolRefAttr`
  - References a module or device by name.
- `params: DictAttr?`
- `conns: ArrayAttr<asdl_ifir.conn>`  (**named-only**)
- `doc: StringAttr?`
- `src: LocAttr?`

### `asdl_ifir.conn` (attr)
- `port: StringAttr`
- `net: StringAttr`

### `asdl_ifir.device` (symbol)
**Attributes**
- `sym_name: StringAttr`
- `ports: ArrayAttr<StringAttr>`
  - Ordered port list.
- `params: DictAttr?`
  - Default parameter values.
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_ifir.backend*`

### `asdl_ifir.backend`
**Attributes**
- `name: StringAttr` (backend key)
- `template: StringAttr` (required)
- `params: DictAttr?` (backend-specific overrides)
- `props: DictAttr?`
  - Additional raw values (from AST backend entries).
- `src: LocAttr?`

---

## Derivation rules (NFIR -> IFIR)
- `asdl_ifir.design.top` is copied from `asdl_nfir.design.top` (if present).
- For each NFIR module:
  - copy `sym_name` and `port_order`.
  - create `asdl_ifir.net` for every NFIR net (names already stripped of `$`).
  - invert NFIR net endpoints into instance conns:
    - for each NFIR net `(net_name, endpoints)`,
      add a conn `{port=<pin>, net=<net_name>}` to the matching instance.
- For each NFIR instance:
  - copy `name`, `ref`, and `params`.
  - conns are populated by the inversion above.
- Devices and their backends are copied 1:1 from NFIR.

---

## Invariants (v0)
- Module names are unique within a design.
- Device names are unique within a design.
- Net names are unique within a module.
- Instance names are unique within a module.
- Each instance's `conns` list has unique `port` names.
- Each `conn.net` must refer to a declared `asdl_ifir.net` in the same module.
- `port_order` is a list of unique names, and each entry corresponds to a net.
- Backend `name` keys are unique per device.
