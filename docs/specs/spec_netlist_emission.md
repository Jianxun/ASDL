# Spec - Netlist Emission v0

## Purpose
Define v0 emission rules from ASDL_NETLIST_IR into backend-selected netlists.
NetlistIR is lowered from the atomized semantic core and already reflects
canonical connectivity.

---

## MVP scope
- Target backend is selected via CLI `--backend` (default `sim.ngspice`).
- Only named connections (no positional conns).
- Subckt parameters are not supported.
- Device parameters are merged and rendered as `k=v` tokens.
- Device variables are merged and exposed as `{var}` placeholders.
- Output extension is determined by backend config (`extension`).
- Input NetlistIR is lowered from AtomizedGraph after pattern expansion;
  emission performs no pattern expansion or connectivity rewriting. The emitter
  may use structured pattern provenance (`pattern_origin` +
  `pattern_expression_table`) for presentation formatting. Module variable
  substitution occurs earlier; NetlistIR carries substituted instance parameter
  values.
- When a design uses view-decorated module variants (`cell@view`), emission is
  realization-based: emit one subckt/module per resolved `(cell, view)` used in
  the design.

---

## Top selection
- Top selection for emission must use the shared top-resolution policy helper
  in strict mode (see ADR-0039).
- If `design.top` is set:
  - resolve by top name
  - when `entry_file_id` is present, the selected top must be resolvable in the
    entry file for emission
  - unresolved top emits `EMIT-001`
- If `design.top` is absent:
  - if `entry_file_id` has exactly one module, use it
  - else if design has exactly one module, use it
  - otherwise emit `EMIT-001`
- Strict emission semantics are diagnostic-producing; permissive non-fatal
  behavior is reserved for traversal/query/view inspection flows.

---

## View-decorated module names
- View decoration is an authoring/resolution concern (see
  `docs/specs/spec_asdl_views.md`).
- Emission consumes already-resolved module selections.
- Emit one realization per unique resolved `(cell, view)`:
  - default/undecorated realization name: `cell`
  - explicit default alias `cell@default` also realizes as `cell`
  - non-default realization name: `cell_<view>` (deterministic, sanitized)
- Instance calls must reference the resolved realization name.
- Emitters must not leak internal `@view` tokens directly into `.subckt` names,
  module call refs, or top placeholders.

---

## Top wrapper handling
- Always emit the top module body.
- Default behavior: emit no `.subckt`/`.ends` wrapper for the top module.
- `--top-as-subckt`: emit the top module with the standard subckt wrapper.

---

## Instance connection ordering
- If instance references a **module**: order nets by the referenced module's
  `port_order`.
- If instance references a **device**: order nets by the device's `ports`.
- Conns are named-only; no positional conns exist in NetlistIR.

---

## Pattern provenance rendering
- NetlistIR net/instance names are atomized literals that define identity and
  connectivity.
- If a net or instance carries `pattern_origin` and the module provides a
  `pattern_expression_table`, the emitter may format the displayed name using
  the base name and pattern parts (for example, applying a backend numeric
  rendering policy).
- Formatting is presentation-only; the emitter must not merge multiple atoms
  back into a single pattern expression or introduce new expansion semantics.
- If provenance metadata is missing or invalid, fall back to the literal NetlistIR
  name (verification should already report invalid provenance).

---

## Device parameter rules

### Merge order (low -> high precedence)
1. `device.params` (defaults)
2. `device.backend.params` (backend overrides)
3. `instance.params` (instance overrides)

### Key restrictions
- `instance.params` must not introduce new keys.
- Any instance param key not present in `device.params` or
  `device.backend.params`:
  - emits a **warning** diagnostic, and
  - is ignored for emission.

### Deterministic parameter ordering
- Start with `device.params` order.
- Append any *new* keys from `device.backend.params` in backend order.
- Append any *new* keys from `instance.params` in instance order.
- Overriding a key does not change its position.

### Value representation
- All param values are raw strings in NetlistIR.
- Boolean values are stringified as `1`/`0` during AST -> NFIR conversion.

### Emission
- Render as space-joined `k=v` tokens (in deterministic order).
- If empty, emit no params and avoid extra whitespace.
- Template usage is explicit; there is no required params placeholder.

Example merge:
```
device.params:       w=1u  l=100n
backend.params:      m=2   l=120n
instance.params:     m=4   nf=2   (nf is invalid, warning + ignored)
result params:       w=1u l=120n m=4
```

---

## Device variable rules

### Merge order (low -> high precedence)
1. `device.variables`
2. `device.backend.variables`

### Key restrictions
- Instance parameters must not introduce keys that match device/backend variables.
- Variable names must not collide with parameter keys or backend props.

### Emission
- Variables are exposed as `{var}` placeholders in backend templates.
- Variables are not rendered into the `{params}` formatted string.

---

## Template contract (devices)
- Each device backend supplies a `template` string.
- Supported placeholders:
  - `{name}` instance name
  - `{ports}` space-joined nets in port order (may be empty)
- `{params}` is deprecated; templates should not rely on it.
- Additional placeholders may be populated from backend `props`.
- Variable keys are available as template placeholders alongside merged parameters.
- Emission is template-driven; the emitter does not inject backend syntax beyond
  device and system-device templates.

---

## System devices (ADR-0006)

### Purpose
System devices define backend-specific structural elements (subcircuit headers, footers, module calls) using the same template mechanism as regular device backends. This decouples backend syntax from emitter logic.

### Reserved names
System device names are prefixed with `__` and are reserved. Regular devices must not use these names.

### Required system devices
Every backend must define the following system devices in `backends.yaml`:

| System Device | Purpose | Required Placeholders | Optional Placeholders |
|---------------|---------|----------------------|----------------------|
| `__subckt_header__` | Non-top module header | `{name}` | `{ports}`, `{file_id}`, `{sym_name}` |
| `__subckt_footer__` | Non-top module footer | - | `{name}` |
| `__subckt_call__` | Module instantiation | `{name}`, `{ports}`, `{ref}` | `{file_id}`, `{sym_name}` |
| `__netlist_header__` | File-level preamble | - | `{backend}`, `{top}`, `{file_id}`, `{top_sym_name}`, `{emit_date}`, `{emit_time}` |
| `__netlist_footer__` | File-level postamble | - | `{backend}`, `{top}`, `{file_id}`, `{top_sym_name}`, `{emit_date}`, `{emit_time}` |

### Backend configuration file
- Location: Determined by environment variable `ASDL_BACKEND_CONFIG`; defaults to `config/backends.yaml`
- Format: YAML with backend sections containing `extension`, `comment_prefix`, and `templates`
- Example for ngspice:
  ```yaml
  sim.ngspice:
    extension: ".spice"
    comment_prefix: "*"
    templates:
      __subckt_header__: ".subckt {name} {ports}"
      __subckt_footer__: ".ends {name}"
      __subckt_call__: "X{name} {ports} {ref}"
      __netlist_header__: ""
      __netlist_footer__: ".end"
  ```
- `extension` is used verbatim by the CLI when `--output` is not provided.
- `comment_prefix` is used by tools that inject optional comment lines; emission is deterministic by default.

### Rendering rules
- System devices are rendered using `_render_system_device()` (similar to `_emit_instance()`)
- Placeholder validation applies (same as device backends)
- Whitespace collapsing applies when `{ports}` is empty
- Missing required system devices emit `MISSING_BACKEND` error and abort emission
- Netlist header/footer are rendered once per file via `__netlist_header__` and
  `__netlist_footer__` (empty templates emit no line)
- `emit_date`/`emit_time` are captured once per netlist emission and formatted
  as `YYYY-MM-DD` and `HH:MM:SS` (local time)

### Top module handling
- If `top_as_subckt` is true: use `__subckt_header__` and `__subckt_footer__`
- Otherwise: emit no subckt wrapper for the top module
- This replaces the previous conditional commenting logic

### Module instantiation
- Module instances use `__subckt_call__` system device instead of hardcoded `X{name} {conns} {ref}` syntax
- Placeholder context:
  - `{name}`: instance name
  - `{ports}`: space-joined connection nets in port order
  - `{ref}`: referenced module name
  - `{file_id}`: referenced module `file_id`
  - `{sym_name}`: referenced module original name (pre-disambiguation)

### File identity placeholders
- `{file_id}` in `__subckt_header__` is the defining module `file_id`.
- `{file_id}` in `__netlist_header__`/`__netlist_footer__` is the entry file `file_id`.
- In end-to-end pipeline execution, `file_id` is expected to be a normalized
  absolute ASDL file path.
- Backends SHOULD include `{file_id}` in subckt header comments for source
  provenance.

### Subckt name disambiguation
- Subckt identifiers must be globally unique in emitted netlists.
- Realization base name:
  - `cell` for undecorated and `cell@default`
  - `cell_<view>` for non-default decorated realizations
- Collision resolution algorithm:
  - process modules in deterministic emission traversal order (do not reorder for
    collision grouping)
  - maintain a global set of already-assigned emitted names
  - assign the base name if unused
  - if used, assign `base__2`, then `base__3`, ... until unused
- This also covers clashes where a decorated realization base name (for example
  `cell_<view>`) collides with an existing undecorated module name.
- The emitted name is used for:
  - `{name}` in `__subckt_header__`
  - `{ref}` in `__subckt_call__`
  - `{top}` in `__netlist_header__`/`__netlist_footer__` when it refers to a
    module
- `{sym_name}` and `{top_sym_name}` always refer to the original module name
  before disambiguation.
- Emitters SHOULD warn when suffix disambiguation is applied and SHOULD emit a
  deterministic logical-to-emitted name mapping artifact.
- When CLI compile logging is enabled, this mapping SHOULD be recorded in the
  compile log JSON (for example under an `emission_name_map` section).

### Validation
- Backend config is loaded and validated at emission time
- Missing required system devices: fatal error (`MISSING_BACKEND`)
- Malformed templates: fatal error (`MALFORMED_TEMPLATE`)
- Unknown placeholders in templates: fatal error (`UNKNOWN_REFERENCE`)

---

## Individual parameter placeholders (T-046)
After merging device/backend/instance params, each key-value pair is available as a template placeholder:
- Example: If merged params are `{L: "0.2u", W: "5u", NF: "2"}`, then `{L}`, `{W}`, `{NF}` are available in templates
- This allows templates like `template: "M{name} {ports} {model} L={L} W={W} NF={NF}"`
- Backward compatibility: `{params}` placeholder still available as formatted string `"L=0.2u W=5u NF=2"`
- Props override params if names collide
