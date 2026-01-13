# Spec — ASDL_IFIR (Instance-First IR) v0 (Emission-Ready)

## Purpose
ASDL_IFIR is an instance-first, netlist-oriented IR with explicit nets and
named-only connections. It is projected from GraphIR after pattern expansion
and is the final pre-emission representation for backend output.

---

## Scope (v0)
- Multi-file designs are supported; symbol identity is `(file_id, name)`.
- Named-only connections (no positional conns).
- Explicit net objects are declared per module.
- Pattern tokens are expanded before IFIR; IFIR names are literal.
- Optional `pattern_origin` metadata may preserve provenance.
- Model names are literals; patterns are forbidden in model names.

---

## Draft ops (xDSL dialect `asdl_ifir`)

### `asdl_ifir.design`
**Role**: top-level container.

**Attributes**
- `top: StringAttr?`
  - Entry module name.
- `entry_file_id: StringAttr?`
  - Canonical file id for the entry file (normalized absolute path).
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_ifir.module*`, `asdl_ifir.device*`

### `asdl_ifir.module` (symbol)
**Attributes**
- `sym_name: StringAttr`
- `file_id: StringAttr`
- `port_order: ArrayAttr<StringAttr>`
  - Ordered list of port names derived from `$` nets (carried from GraphIR).
  - Port names are stored without the `$` prefix and are literal.
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_ifir.net*`, `asdl_ifir.instance*`

### `asdl_ifir.net`
**Attributes**
- `name: StringAttr`
  - Net name; literal (post-expansion).
- `net_type: StringAttr?`
- `pattern_origin: StringAttr?`
- `src: LocAttr?`

### `asdl_ifir.instance`
**Attributes**
- `name: StringAttr`
  - Instance name; literal (post-expansion).
- `ref: StringAttr`
  - References a module or device by unqualified name.
- `ref_file_id: StringAttr`
  - Resolved file id for the referenced module/device definition.
- `params: DictAttr?`
- `conns: ArrayAttr<asdl_ifir.conn>`  (**named-only**)
- `pattern_origin: StringAttr?`
- `doc: StringAttr?`
- `src: LocAttr?`

### `asdl_ifir.conn` (attr)
- `port: StringAttr`
  - Pin name; literal (post-expansion).
- `net: StringAttr`
  - Net name; literal (post-expansion).

### `asdl_ifir.device` (symbol)
**Attributes**
- `sym_name: StringAttr`
- `file_id: StringAttr`
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

## Derivation rules (GraphIR -> IFIR)
- GraphIR verification must run and succeed before projection.
- `asdl_ifir.design.top` is the entry module name (if entry is set).
- `asdl_ifir.design.entry_file_id` is the entry module `file_id` (if entry is set).
- For each GraphIR module:
  - copy `sym_name`, `file_id`, and `port_order` from module attributes.
  - expand pattern bundles into literal atoms and create one `asdl_ifir.net`
    per net atom; set `pattern_origin` when derived from a pattern token.
  - invert GraphIR endpoints into instance conns:
    - for each endpoint atom, add a conn `{port=<port_literal>, net=<net_literal>}`
      to the matching instance.
- For each GraphIR instance:
  - create one IFIR instance per atomized name; set `pattern_origin` when derived
    from a pattern token.
  - set `ref` and `ref_file_id` from the resolved `SymbolRef`.
- Devices and their backends are copied 1:1 from GraphIR, including `file_id`.

---

## Verification (IFIR, pre-emission)
- All net, instance, and port names are literal; pattern delimiters are forbidden.
- Net names are unique within a module.
- Instance names are unique within a module.
- Each instance's `conns` list has unique `port` names.
- Each `conn.net` refers to a declared `asdl_ifir.net` in the same module.
- `port_order` is a list of unique names, and each entry corresponds to a net.

---

## Elaboration (pre-emission)
- No elaboration occurs after IFIR projection; emission consumes IFIR as-is.

---

## Invariants (v0)
- Module names are unique per `file_id`.
- Device names are unique per `file_id`.
- Net names are unique within a module.
- Instance names are unique within a module.
- Each instance's `conns` list has unique `port` names.
- Each `conn.net` refers to a declared `asdl_ifir.net` in the same module.
- `port_order` is a list of unique names, and each entry corresponds to a net.
- Backend `name` keys are unique per device.
- `pattern_origin` does not affect identity; it is provenance-only.
