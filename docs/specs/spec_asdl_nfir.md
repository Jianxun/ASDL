# Spec C — ASDL_NFIR (Net-First IR) v0

## Purpose
ASDL_NFIR captures explicit net-first topology derived from the Tier-1 authoring
AST. It is the bridge between authoring and the canonical ASDL_CIR.

---

## Role
- Nets own endpoint lists (connectivity is net-first).
- Names are represented as **basename + optional pattern domain** until
  elaboration (post-MVP).
- View selection and compatibility metadata are out of scope.

---

## MVP constraints
- Only explicit net/instance names (no pattern or wildcard sugar).
- No imports or exports.
- No inline pin-bind sugar; connectivity is declared in `nets:` only.

---

## Draft ops (xDSL dialect `asdl_nfir`)
This is a minimal draft to anchor MVP implementation; details may evolve.

### `asdl_nfir.design`
**Role**: top-level container.

**Region**
- contains: `asdl_nfir.module*`

### `asdl_nfir.module` (symbol)
**Attributes**
- `sym_name: StringAttr`
- `doc: StringAttr?`
- `port_order: ArrayAttr<StringAttr>` (derived from `$` nets)
- `src: LocAttr?`

**Region**
- contains: `asdl_nfir.net*`, `asdl_nfir.instance*`

### `asdl_nfir.net`
**Attributes**
- `name: StringAttr`
- `endpoints: ArrayAttr<asdl_nfir.endpoint>`
- `src: LocAttr?`

### `asdl_nfir.endpoint` (attr)
**Fields**
- `inst: StringAttr`
- `pin: StringAttr`

### `asdl_nfir.instance`
**Attributes**
- `name: StringAttr`
- `ref: SymbolRefAttr` (module or device)
- `params: DictAttr?`
- `doc: StringAttr?`
- `src: LocAttr?`

---

## Invariants (v0)
- Net names are unique within a module.
- Instance names are unique within a module.
- Each endpoint `(inst, pin)` binds to **at most one** net.
- Ports are derived only from `$`-prefixed net names; order follows `port_order`.
