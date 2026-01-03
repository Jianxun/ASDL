# Spec - ASDL_A (Authoring AST) v0 (MVP, Net-First, Minimal)

## Purpose
A minimal, schema-validated AST for MVP authoring. It preserves raw strings and
ordered mappings but performs no semantic resolution.

---

## MVP scope
- Single self-contained ASDL file (no imports/includes).
- Top-level fields are limited to `top`, `modules`, `devices`.
- Modules contain only `instances` and `nets`.
- No `exports` block.
- Connectivity is declared only in `nets` (no inline pin-binds).
- Names and endpoints are explicit (no wildcards or pattern domains).

---

## Top-Level: `AsdlDocument`

### Fields
- `top: Optional[str]`
  - Entry module name.
  - Required if more than one module exists; otherwise optional.
- `modules: Optional[Dict[str, ModuleDecl]]`
  - Map of module name -> module definition.
- `devices: Optional[Dict[str, DeviceDecl]]`
  - Map of device name -> device definition.

### Notes
- At least one of `modules` or `devices` must be present.

---

## `ModuleDecl`

### Fields
- `instances: Optional[InstancesBlock]`
- `nets: Optional[NetsBlock]`

### Notes
- Connectivity is net-first: `nets` own endpoint lists.
- Module ports are derived from `$`-prefixed net names.
- Port order is the appearance order of `$` nets in `nets`.

---

## `InstancesBlock`
Single authoring style for MVP: flat map.

### Style -- flat map
```yaml
instances:
  MN_IN: nfet_3p3 m=8
  MP_LOAD: pfet_3p3 m=2
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
- **MVP token form**: `<key>=<value>` (no spaces around `=`).
- Inline pin-bindings are not permitted in MVP.

---

## `NetsBlock`

### AST shape
- `NetsBlock` is an ordered mapping: `Dict[str, List[str]]`.

#### `EndpointListExpr`
- **Type**: `List[str]` (raw endpoint tokens).
- **Grammar (MVP)**: `<InstName>.<PinName>` tokens only.
- Example:
  ```yaml
  nets:
    $VIN:
      - MN_IN.G
    VSS:
      - MN_IN.S
      - MTAIL.S
  ```

### Notes
- `$` on the net name marks an exported port.
- Port order is the appearance order of `$` nets in `nets`.

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
- Additional keys are permitted and treated as raw values available as
  `{placeholders}` in `template` (e.g., `model`).

---

## Hard Requirements (AST-level)
- `top` is required if more than one module exists.
- `backends` must be a non-empty map for each device.
- `DeviceBackendDecl.template` must exist and be a string.
- `InstancesBlock` entries must be `InstanceExpr` strings.
- `NetsBlock` values must be `EndpointListExpr` lists of strings.
- No `exports` key is permitted under `ModuleDecl` in MVP.
- No imports/includes are permitted in the document in MVP.
