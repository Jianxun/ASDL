# Spec D — ASDL_IFIR (Instance-First IR) v0 (Pattern-Preserving)

## Purpose
ASDL_IFIR is an instance-first, netlist-oriented IR with explicit nets and
named-only connections. It preserves pattern tokens and is the final pre-
elaboration representation before backend emission.

---

## Scope (v0)
- Multi-file designs are supported; symbol identity is `(file_id, name)`.
- Named-only connections (no positional conns).
- Explicit net objects are declared per module.
- Pattern tokens may appear only in instance names, net names, and endpoint
  tokens (instance name and pin name).
- Model names are literals; patterns are forbidden in model names.

---

## Draft ops (xDSL dialect `asdl_ifir`)

### `asdl_ifir.design`
**Role**: top-level container.

**Attributes**
- `top: StringAttr?`
  - Entry module name (from AST `top`).
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
  - Ordered list of port names derived from `$` nets in AST.
  - Port names are stored without the `$` prefix and may include pattern tokens.
  - `;` is forbidden in `$` net expressions.
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_ifir.net*`, `asdl_ifir.instance*`

### `asdl_ifir.net`
**Attributes**
- `name: StringAttr`
  - Net name; may include pattern tokens.
- `expansion_len: IntegerAttr`
  - Total expansion length of `name` (1 for literals).
- `net_type: StringAttr?`
- `src: LocAttr?`

### `asdl_ifir.instance`
**Attributes**
- `name: StringAttr`
  - Instance name; may include pattern tokens.
- `expansion_len: IntegerAttr`
  - Total expansion length of `name` (1 for literals).
- `ref: StringAttr`
  - References a module or device by unqualified name.
- `ref_file_id: StringAttr`
  - Resolved file id for the referenced module/device definition.
- `params: DictAttr?`
- `conns: ArrayAttr<asdl_ifir.conn>`  (**named-only**)
- `doc: StringAttr?`
- `src: LocAttr?`

### `asdl_ifir.conn` (attr)
- `port: StringAttr`
  - Pin name token; may include pattern tokens.
- `port_len: IntegerAttr`
  - Total expansion length of `port` (1 for literals).
- `net: StringAttr`
  - Net name token (may include pattern tokens).

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

## Derivation rules (NFIR -> IFIR)
- NFIR verification must run and succeed before lowering.
- `asdl_ifir.design.top` is copied from `asdl_nfir.design.top` (if present).
- `asdl_ifir.design.entry_file_id` is copied from `asdl_nfir.design.entry_file_id`.
- For each NFIR module:
  - copy `sym_name`, `file_id`, and `port_order`.
  - create `asdl_ifir.net` for every NFIR net (names already stripped of `$`).
  - copy `expansion_len` from NFIR net `name`.
  - invert NFIR net endpoints into instance conns:
    - for each NFIR net `(net_name, endpoints)`,
      add a conn `{port=<pin>, port_len=<pin_len>, net=<net_name>}` to the
      matching instance.
- For each NFIR instance:
  - copy `name`, `expansion_len`, `ref`, `ref_file_id`, and `params`.
  - conns are populated by the inversion above.
- Devices and their backends are copied 1:1 from NFIR, including `file_id`.

---

## Verification (IFIR, pre-elaboration)
- Binding compares total expansion length; splicing is flattened.
- If a net expands to length **N > 1**, every bound endpoint must expand to **N**;
  bind by index.
- If a net is scalar (length **1**), it may bind to endpoints of any length;
  each expanded endpoint binds to that single net.
- Endpoint expansion length is computed as:
  - `instance.expansion_len * conn.port_len`.
- Every scalar endpoint atom binds to exactly one net.
- Equivalence checks use fully expanded string tokens; binding verification and
  elaboration must share the same equivalence helper.
- `expansion_len` and `port_len` must be <= 10k and match the expansion engine.

---

## Elaboration (pre-emission)
- A dedicated pass expands all pattern tokens into explicit names/endpoints.
- Emission runs only on the elaborated form.

---

## Invariants (v0)
- Module names are unique per `file_id`.
- Device names are unique per `file_id`.
- Net names are unique within a module (post-verification).
- Instance names are unique within a module (post-verification).
- Each instance's `conns` list has unique `port` names (post-verification).
- Each `conn.net` must refer to a declared `asdl_ifir.net` in the same module
  (using expanded-token equivalence).
- `port_order` is a list of unique names, and each entry corresponds to a net.
- Backend `name` keys are unique per device.
