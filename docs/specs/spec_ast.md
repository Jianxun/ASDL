# Spec A — ASDL_A (Tier-1 Authoring AST) v0.3 (Net-First)

## Purpose
A **loss-minimizing, schema-validated AST** for Tier-1 authoring YAML.
- Validates **shape/types** only.
- Preserves **raw strings** for inline instance expressions, endpoint tokens, and templates.
- Does **not** perform semantic resolution (imports, symbol lookup, domain expansion, ERC).
- Represents the net-first authoring surface: **modules + devices + optional `top`**.

## Conventions
- **Plural nouns** for collections: `modules`, `devices`, `instances`, `nets`, `exports`, `backends`, `params`.
- Ordered mappings preserve source order when it matters (notably `nets` and `exports`).
- Names are raw strings with existing naming rules; validation is deferred.
- Comments/docstrings/groups are YAML comments and are **not** represented in AST fields.

---

## Top-Level: `AsdlDocument`

### Fields
- `top: Optional[str]`
  - Entry module name.
  - Required if **multiple modules** exist; otherwise optional.
- `modules: Optional[Dict[str, ModuleDecl]]`
  - Map of module name → module definition.
- `devices: Optional[Dict[str, DeviceDecl]]`
  - Map of device name → device definition.

### Notes
- At least one of `modules` or `devices` must be present.
- Recommended: a name must not appear in both `modules` and `devices`.

---

## `ModuleDecl`

### Fields
- `instances: Optional[InstancesBlock]`
- `nets: Optional[NetsBlock]`
- `exports: Optional[ExportsBlock]`

### Notes
- Connectivity is net-first: `nets` own endpoint lists.
- Module ports are derived from `$`-prefixed net names (plus forwarded ports from `exports`).

---

## `InstancesBlock`
Single authoring style for MVP: flat map.

### Style A — flat map
```yaml
instances:
  MN_IN<P,N>: nfet_3p3 m=8 (B:$VSS)
  MP_LOAD<P,N>: pfet_3p3 m=2 (B:$VDD)
```

### AST shape
- `InstancesBlock` is an ordered mapping: `Dict[str, InstanceExpr]`.

#### `InstanceExpr`
- **Type**: `str` (raw inline instance expression).
- **Grammar (opaque at AST)**:
  ```
  <TypeName> <ParamTokens...> ( <PinBind>... )?
  ```
- `ParamTokens` are preserved as raw text.
- Inline pin-bindings are preserved as raw text; conflicts are resolved later.

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
- `*`, `<...>`, `[...]`, and `;` pattern/domain markers are preserved as raw tokens for later expansion.

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
- `params: Optional[Dict[str, ParamValue]]`
  - Default parameter values.
- `backends: Dict[str, DeviceBackendDecl]`
  - Backend-specific template entries; must be non-empty.

### `ParamValue`
- `int | float | bool | str`

---

## `DeviceBackendDecl`

### Fields
- `template: str` (required)
- `params: Optional[Dict[str, ParamValue]]` (optional override of shared defaults)
- Additional keys are permitted and treated as raw values available as `{placeholders}`
  in `template` (e.g., `model`).

---

## Hard Requirements (AST-level)
- `top` is required if more than one module exists.
- `backends` must be a **non-empty** map for each device.
- `DeviceBackendDecl.template` must exist and be a string.
- `InstancesBlock` entries must be `InstanceExpr` strings.
- `NetsBlock` values must be `EndpointListExpr` lists of strings.

---

## Deferred to IR verification / passes
- Name resolution (module/device lookup, instance refs).
- Domain and wildcard expansion (`*`, `<...>`, `[...]`).
- Inline pin-bind parsing and conflict detection vs `nets`.
- Export forwarding resolution and collision checks.
- Endpoint uniqueness checks (an endpoint bound to multiple nets).
- Template placeholder validity and backend-specific constraints.
