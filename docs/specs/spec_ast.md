# Spec — ASDL_A (Authoring AST) v0.3 (Net-First)

## Purpose
A **loss-minimizing, schema-validated AST** for Tier-1 authoring YAML.
- Validates **shape/types** only.
- Preserves **raw strings** for inline instance expressions, endpoint tokens, and templates.
- Does **not** perform semantic resolution (imports, symbol lookup, domain expansion, ERC).
- Represents the net-first authoring surface: **modules + devices + optional `top`**.

## Conventions
- **Plural nouns** for collections: `modules`, `devices`, `instances`, `nets`, `exports`, `backends`, `parameters`, `variables`.
- Ordered mappings preserve source order when it matters (notably `nets` and `exports`).
- Literal names must match `[A-Za-z_][A-Za-z0-9_]*`; pattern delimiters (`<`, `>`, `|`, `:`, `;`)
  are reserved and forbidden in literals.
- Module declaration keys may additionally use view-decorated form
  `cell@view` per `docs/specs/spec_asdl_views.md`, where both `cell` and
  `view` follow the literal-name regex.
- Qualified references may use `ns.symbol` in inline instance expressions only;
  both `ns` and `symbol` must match the literal name regex.
- Names are raw strings; semantic validation is deferred to verification passes.
- Comments/docstrings/groups are YAML comments and are **not** represented in AST fields.

---

## Top-Level: `AsdlDocument`

### Fields
- `imports: Optional[Dict[str, str]]`
  - Map of namespace → import path (raw string).
  - Namespaces must match `[A-Za-z_][A-Za-z0-9_]*`.
- `top: Optional[str]`
  - Entry module name.
  - When decorated symbols are present, `top` refers to logical `cell` name
    (view selection is deferred to binding resolution).
  - Required if **multiple modules** exist; otherwise optional.
- `modules: Optional[Dict[str, ModuleDecl]]`
  - Map of module symbol → module definition.
  - Module symbol may be `cell` or `cell@view` (single `@` max).
- `devices: Optional[Dict[str, DeviceDecl]]`
  - Map of device name → device definition.

### Notes
- At least one of `modules` or `devices` must be present (import-only files are invalid).
- Recommended: a name must not appear in both `modules` and `devices`.

---

## `ModuleDecl`

### Fields
- `instances: Optional[InstancesBlock]`
- `nets: Optional[NetsBlock]`
- `patterns: Optional[PatternsBlock]`
- `instance_defaults: Optional[InstanceDefaultsBlock]`
- `exports: Optional[ExportsBlock]`
- `parameters: Optional[Dict[str, ParamValue]]`
- `variables: Optional[Dict[str, ParamValue]]`

### Notes
- Connectivity is net-first: `nets` own endpoint lists.
- `instance_defaults` provide default bindings per instance `ref` and are
  overridden by explicit `nets` bindings (override warnings are deferred).
- Module ports are derived from `$`-prefixed net names (plus forwarded ports from `exports`).
- `parameters` define module-level default parameter values used when the
  module is emitted as a subckt definition (for example header parameter
  clauses); backend syntax is handled by system templates.
- `variables` are module-local constants usable only in instance parameter values
  via `{var}` placeholders; recursive references are invalid.

---

## `InstancesBlock`
Single authoring style for MVP: flat map.

### Style A — flat map
```yaml
instances:
  MN_IN<P|N>: nfet_3p3 m=8
  MP_LOAD<P|N>: pfet_3p3 m=2
```

### AST shape
- `InstancesBlock` is an ordered mapping: `Dict[str, InstanceExpr]`.

#### `InstanceExpr`
- **Type**: `str` (raw inline instance expression).
- **Grammar (opaque at AST)**:
  ```
  <TypeName> <ParamTokens...>
  ```
- `ParamTokens` are preserved as raw text.
- `ParamTokens` may include pattern syntax; expansion uses broadcast/zip semantics
  after instance-name expansion (deferred).
- `<TypeName>` may be either `symbol` or `ns.symbol`; pattern syntax is forbidden.
- Param values may reference module variables via `{var}` placeholders. Substitution
  is raw string replacement and occurs before parameter pattern expansion.

---

---

## `PatternsBlock`

### AST shape
- `PatternsBlock` is an ordered mapping: `Dict[str, PatternDecl]`.
- `PatternDecl` is either:
  - a string **group token**: `<...>` using `|` for enums or `:` for ranges, or
  - an object with:
    - `expr: str` (required group token)
    - `tag: Optional[str]` (axis identifier override)

Example:
```yaml
patterns:
  BUS25: <25:1>
  BUS0:
    expr: <24:0>
    tag: BUS
```

### Notes
- Named pattern references use `<@name>`.
- `patterns` are module-local only.
- Named patterns must not reference other named patterns.
- Pattern names must match `[A-Za-z_][A-Za-z0-9_]*`.
- `expr` must be a single group token (`<...>`); `<@...>` is not allowed in `expr`.
- `tag`, when present, must match `[A-Za-z_][A-Za-z0-9_]*`.
- `axis_id = tag` if present, otherwise `axis_id = pattern name`.
- If multiple patterns share an `axis_id`, their expansion lengths must match
  (validated at definition time).

---

## `InstanceDefaultsBlock`

### AST shape
- `InstanceDefaultsBlock` is an ordered mapping: `Dict[str, InstanceDefaultsDecl]`.

#### `InstanceDefaultsDecl`
- `bindings: Dict[str, str]`
  - Map of port name -> net token.
  - Port names must be literal names (no patterns).
  - Net tokens may include pattern syntax and `$` prefixes.

### Notes
- Defaults apply to all instances with matching `ref`.
- Explicit `nets` bindings override defaults; overrides may emit warnings.

---

## `NetsBlock`

### AST shape
- `NetsBlock` is an ordered mapping: `Dict[str, List[str]]`.

#### `EndpointListExpr`
- **Type**: `List[str]` (raw endpoint tokens).
- Example:
  ```yaml
  nets:
    $VIN<P|N>:
      - MN_IN<P|N>.G
    VSS:
      - MN_CS*.S
      - MTAIL.S
  ```

### Notes
- `$` on the net name marks an **exported port**.
- Port order is the appearance order of `$` nets in `nets`, followed by forwarded ports from `exports`.
- `*`, `<...>`, `<@name>`, and `;` pattern/domain markers are preserved as raw tokens for later expansion.
- `$` net names may include pattern syntax, but `;` is forbidden in `$` net expressions.
- Endpoint tokens may be prefixed with `!` to suppress default-override warnings; `!`
  is not part of the endpoint name.

---

## `ExportsBlock`

### AST shape
- Mapping: `Dict[str, List[str]]`
  - Key: instance name (must resolve to a module instance later).
  - Value: list of glob patterns (`*` wildcard), with optional `-` negation.

### Notes
- `$` prefix in patterns is optional.
- Only exported child ports are eligible for forwarding.
- No renaming is supported in `exports` (use explicit `nets` entries for renames).

---

## `DeviceDecl`

### Fields
- `ports: Optional[List[str]]`
  - Ordered port list; may be omitted for portless devices.
- `parameters: Optional[Dict[str, ParamValue]]`
  - Default parameter values.
- `variables: Optional[Dict[str, ParamValue]]`
  - Device-local constants (immutable at instantiation).
- `backends: Dict[str, DeviceBackendDecl]`
  - Backend-specific template entries; must be non-empty.

### `ParamValue`
- `int | float | bool | str`

---

## `DeviceBackendDecl`

### Fields
- `template: str` (required)
- `parameters: Optional[Dict[str, ParamValue]]` (optional override of shared defaults)
- `variables: Optional[Dict[str, ParamValue]]` (optional backend-local constants)
- Additional keys are permitted and treated as raw values available as `{placeholders}`
  in `template` (e.g., `model`).

---

## Hard Requirements (AST-level)
- `top` is required if more than one module exists.
- At least one of `modules` or `devices` must be present.
- `backends` must be a **non-empty** map for each device.
- `DeviceBackendDecl.template` must exist and be a string.
- `InstancesBlock` entries must be `InstanceExpr` strings.
- `NetsBlock` values must be `EndpointListExpr` lists of strings.
- `PatternsBlock` values must be strings or `{expr, tag}` objects; `expr` is required
  and `tag` is optional, and no other keys are permitted.
- `PatternsBlock` entries sharing an `axis_id` must have identical expansion lengths.
- `InstanceDefaultsDecl.bindings` values must be strings.

---

## Deferred to IR verification / passes
- Name resolution (module/device lookup, instance refs).
- Named pattern expansion (`<@name>`) and pattern expansion/binding verification (`<...>` with `|`/`:` and `;`); enforce expansion size limits.
- Patterned parameter expansion (broadcast/zip; no cross-product).
- Module variable substitution (`{var}`) in instance parameter values, including
  undefined variable diagnostics and recursion detection.
- Apply `instance_defaults` and emit override warnings (suppressed by `!`).
- Export forwarding resolution and collision checks.
- Endpoint uniqueness checks (an endpoint bound to multiple nets).
- Template placeholder validity and backend-specific constraints.
