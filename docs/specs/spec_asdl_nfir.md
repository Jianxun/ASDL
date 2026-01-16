# Spec — ASDL_NFIR (Net-First IR) v0 (Pattern-Preserving)

## Purpose
ASDL_NFIR captures explicit net-first topology derived from the authoring
AST. It preserves pattern tokens and exists as an optional projection used for
roundtrip/debugging rather than as a required pipeline stage.

---

## Role
- NFIR is a projection-only IR; the canonical pipeline lowers AST -> GraphIR.
- Nets own endpoint lists (connectivity is net-first).
- Names may include pattern tokens; no expansion occurs in NFIR.
- Port order is explicit and preserves `$` net tokens (without the `$`).
- Model names are literals; patterns are forbidden in model names.

---

## Scope (v0)
- Multi-file designs are supported; symbol identity is `(file_id, name)`.
- Pattern tokens allowed only in instance names, net names, and endpoint tokens
  (instance name and pin name).
- No view system or backend selection semantics.

---

## Draft ops (xDSL dialect `asdl_nfir`)

### `asdl_nfir.design`
**Role**: top-level container.

**Attributes**
- `top: StringAttr?`
  - Entry module name (from AST `top`).
- `entry_file_id: StringAttr?`
  - Canonical file id for the entry file (normalized absolute path).
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_nfir.module*`, `asdl_nfir.device*`

### `asdl_nfir.module` (symbol)
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
- contains: `asdl_nfir.net*`, `asdl_nfir.instance*`

### `asdl_nfir.net`
**Attributes**
- `name: StringAttr`
  - Net name (no `$` prefix); may include pattern tokens.
- `expansion_len: IntegerAttr`
  - Total expansion length of `name` (1 for literals).
- `endpoints: ArrayAttr<asdl_nfir.endpoint>`
- `src: LocAttr?`

### `asdl_nfir.endpoint` (attr)
**Fields**
- `inst: StringAttr`
  - Instance name token; may include pattern tokens.
- `inst_len: IntegerAttr`
  - Total expansion length of `inst` (1 for literals).
- `pin: StringAttr`
  - Pin name token; may include pattern tokens.
- `pin_len: IntegerAttr`
  - Total expansion length of `pin` (1 for literals).

### `asdl_nfir.instance`
**Attributes**
- `name: StringAttr`
  - Instance name; may include pattern tokens.
- `expansion_len: IntegerAttr`
  - Total expansion length of `name` (1 for literals).
- `ref: StringAttr`
  - Model name parsed from the AST instance expression; unqualified symbol name.
- `ref_file_id: StringAttr`
  - Resolved file id for the referenced module/device definition.
- `params: DictAttr?`
  - Key/value parameters parsed from the AST instance expression.
  - Values are stored as raw strings after module variable substitution.
- `doc: StringAttr?`
- `src: LocAttr?`

### `asdl_nfir.device` (symbol)
**Attributes**
- `sym_name: StringAttr`
- `file_id: StringAttr`
- `ports: ArrayAttr<StringAttr>`
  - Ordered port list.
- `params: DictAttr?`
  - Default parameter values.
- `variables: DictAttr?`
  - Device-local constants (immutable at instantiation).
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_nfir.backend*`

### `asdl_nfir.backend`
**Attributes**
- `name: StringAttr` (backend key)
- `template: StringAttr` (required)
- `params: DictAttr?` (backend-specific overrides)
- `variables: DictAttr?` (backend-local constants)
- `props: DictAttr?`
  - Additional raw values (from AST backend entries).
- `src: LocAttr?`

---

## Derivation rules (AST -> NFIR)
- `asdl_nfir.design.top` is copied from AST `top` (if present).
- `asdl_nfir.design.entry_file_id` is the canonical `file_id` of the entry file.
- `top` resolution is scoped to `entry_file_id`; same-name modules in other files
  do not satisfy the entry top.
- For each `$` net in AST:
  - strip the `$` prefix for the NFIR net name.
  - append the stripped name (verbatim pattern token) to `port_order`.
- Non-port nets must not start with `$` in NFIR.
- Parse `InstanceExpr` as:
  - first token is the type token (`symbol` or `ns.symbol`),
  - remaining tokens must be `<key>=<value>` pairs,
  - store params as a dict of raw strings.
- If the type token is qualified (`ns.symbol`), store `symbol` in `ref` and
  `ref_file_id` from name resolution. Unqualified refs use the current file's
  `file_id`.
- Instances store `ref_file_id` from import-aware name resolution.
- Devices and their backends are copied 1:1 from AST and tagged with `file_id`.
- Compute and attach `expansion_len`, `inst_len`, and `pin_len` using the
  pattern expansion rules (length only; no expansion is emitted).

---

## Required verification pass (NFIR)
Must run and succeed before GraphIR construction.
- Enforce literal name regex (`[A-Za-z_][A-Za-z0-9_]*`).
- Patterns are allowed only in instance names, net names, and endpoint tokens
  (instance name and pin name); forbidden in model names.
- `$` nets preserve pattern tokens but must not contain `;`.
- Expansion length per token must be <= 10k and match the expansion engine.
- Endpoint `inst` references must resolve to an NFIR instance name (using
  expanded-token equivalence).
- Endpoint expansion length is derived as `inst_len * pin_len` (left-to-right).

---

## Diagnostics (AST -> NFIR conversion)
- `IR-001`: invalid instance param token (not `key=value`); conversion returns no design.
- `IR-002`: invalid endpoint token (not `inst.pin`); conversion returns no design.

---

## Invariants (v0)
- Net names are unique within a module.
- Instance names are unique within a module.
- Each endpoint `(inst, pin)` binds to at most one net (post-verification).
- `port_order` is a list of unique names, and each entry corresponds to a net.
- `ref` is non-empty and literal for every instance.
- Module names are unique per `file_id`.
- Device names are unique per `file_id`.
- Backend `name` keys are unique per device.
