# Spec - ASDL_NFIR (Net-First IR) v0 (MVP, AST-Aligned)

## Purpose
ASDL_NFIR is a minimal net-first IR that mirrors the authoring AST structure while
making port order explicit. It performs no semantic elaboration beyond port
list extraction.

---

## MVP scope
- Self-contained design (no imports/exports/includes).
- Pattern tokens may appear in instance names, net names, and endpoint tokens;
  atomization into single-atom patterns is deferred to a later pass.
- Pattern tokens may omit a literal prefix (e.g., `<INP|INN>` or `[2:0]`).
- No inline pin-binds; connectivity is declared only in `nets`.
- NFIR mirrors AST 1:1, except that:
  - a deterministic `port_order` is stored, and
  - instance expressions are parsed into model name + params.

---

## Draft ops (xDSL dialect `asdl_nfir`)

### `asdl_nfir.design`
**Role**: top-level container.

**Attributes**
- `top: StringAttr?`
  - Entry module name (from AST `top`).

**Region**
- contains: `asdl_nfir.module*`, `asdl_nfir.device*`

### `asdl_nfir.module` (symbol)
**Attributes**
- `sym_name: StringAttr`
- `port_order: ArrayAttr<StringAttr>`
  - Ordered list of port names derived from `$` nets in AST.
  - Port names are stored without the `$` prefix.
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_nfir.net*`, `asdl_nfir.instance*`

### `asdl_nfir.net`
**Attributes**
- `name: StringAttr`
  - Canonical net name (no `$` prefix).
- `endpoints: ArrayAttr<asdl_nfir.endpoint>`
- `src: LocAttr?`

### `asdl_nfir.endpoint` (attr)
**Fields**
- `inst: StringAttr`
- `pin: StringAttr`

### `asdl_nfir.instance`
**Attributes**
- `name: StringAttr`
- `ref: StringAttr`
  - Model name parsed from the AST instance expression.
- `params: DictAttr?`
  - Key/value parameters parsed from the AST instance expression.
  - Values are stored as raw strings.
- `doc: StringAttr?`
- `src: LocAttr?`

### `asdl_nfir.device` (symbol)
**Attributes**
- `sym_name: StringAttr`
- `ports: ArrayAttr<StringAttr>`
  - Ordered port list.
- `params: DictAttr?`
  - Default parameter values.
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_nfir.backend*`

### `asdl_nfir.backend`
**Attributes**
- `name: StringAttr` (backend key)
- `template: StringAttr` (required)
- `params: DictAttr?` (backend-specific overrides)
- `props: DictAttr?`
  - Additional raw values (from AST backend entries).
- `src: LocAttr?`

---

## Derivation rules (AST -> NFIR)
- `asdl_nfir.design.top` is copied from AST `top` (if present).
- For each `$` net in AST, strip the `$` prefix for the NFIR net name.
- `port_order` is the ordered list of those stripped names, in AST `nets` order.
- Non-port nets must not start with `$` in NFIR.
- Parse `InstanceExpr` as:
  - first token is `ref` (model name),
  - remaining tokens must be `<key>=<value>` pairs,
  - store params as a dict of raw strings.
- Devices and their backends are copied 1:1 from AST.

---

## Diagnostics (AST -> NFIR conversion)
- `IR-001`: invalid instance param token (not `key=value`); conversion returns no design.
- `IR-002`: invalid endpoint token (not `inst.pin`); conversion returns no design.

---

## Invariants (v0)
- Net names are unique within a module.
- Instance names are unique within a module.
- Each endpoint `(inst, pin)` binds to at most one net.
- Every endpoint `inst` must resolve to a declared instance atom after pattern
  atomization (endpoint atoms must be a subset of instance atoms).
- Literal names produced by atomization must be unique within instance names
  and within net names; collisions are errors even across different pattern
  origins.
- `port_order` is a list of unique names, and each entry corresponds to a net.
- `ref` is non-empty for every instance.
- Device names are unique within a design.
- Backend `name` keys are unique per device.
