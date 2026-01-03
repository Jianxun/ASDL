# ADR-0006: System Devices for Backend Structural Templates

**Status**: Accepted
**Date**: 2026-01-03

---

## Context

The ngspice emitter (`src/asdl/emit/ngspice.py`) currently has backend-specific syntax hardcoded in several places:

1. **Subcircuit delimiters**: `.subckt {name} {ports}` and `.ends {name}` in `_emit_module()` and `_format_subckt_line()`
2. **Top module handling**: Conditional commenting logic (`*` prefix) for top modules
3. **Module instantiation**: `X{name} {conns} {ref}` syntax in `_emit_instance()`

This tight coupling to ngspice syntax makes it difficult to:
- Support additional backends (e.g., spectre, hspice) without duplicating emitter logic
- Customize output format per backend
- Test structural template variations independently

Meanwhile, **device instances** already use a flexible template system (`backend.template` with placeholders), which works well and supports backend-specific syntax cleanly.

---

## Decision

Introduce **system devices**: reserved device names prefixed with `__` that define backend-specific structural elements. System devices are defined in an external **backend configuration file** (`backends.yaml`) and use the same template placeholder mechanism as regular device backends.

### Required system devices

All backends must define these system devices:

| System Device | Purpose | Required Placeholders |
|---------------|---------|----------------------|
| `__subckt_header__` | Non-top module header | `{name}`, `{ports}` (optional) |
| `__subckt_footer__` | Non-top module footer | `{name}` |
| `__top_header__` | Top module header | `{name}`, `{ports}` (optional) |
| `__top_footer__` | Top module footer | `{name}` |
| `__subckt_call__` | Module instantiation | `{name}`, `{ports}`, `{ref}` |

### Optional system devices

Backends may define these for additional customization:

| System Device | Purpose | Placeholders |
|---------------|---------|--------------|
| `__netlist_header__` | File-level preamble | `{backend}`, `{top}` |
| `__netlist_footer__` | File-level postamble | `{backend}`, `{top}` |

### Backend configuration file

- Location: Determined by environment variable (e.g., `ASDL_BACKEND_CONFIG`); defaults to `config/backends.yaml`
- Format: YAML with backend sections containing `system_devices` entries
- Example:
  ```yaml
  ngspice:
    system_devices:
      __subckt_header__:
        template: ".subckt {name} {ports}"
      __subckt_footer__:
        template: ".ends {name}"
      __top_header__:
        template: "*.subckt {name} {ports}"
      __top_footer__:
        template: "*.ends {name}"
      __subckt_call__:
        template: "X{name} {ports} {ref}"
  ```

### Emitter changes

1. Load backend config at emission time
2. Validate that required system devices are present (fatal error if missing)
3. Replace hardcoded structural syntax with `_render_system_device()` calls
4. Remove `_format_subckt_line()` and inline header/footer string literals

---

## Consequences

### Positive

1. **Backend extensibility**: New backends (spectre, hspice, etc.) can be added by defining system device templates in `backends.yaml` without modifying emitter code
2. **Consistency**: All rendering (devices and structure) uses the same template system
3. **Testability**: System device templates can be unit tested independently
4. **Separation of concerns**: Backend syntax lives in config files, not Python code

### Negative

1. **Configuration burden**: Every backend must define 5+ system devices (vs. hardcoding)
2. **Indirection**: Structural syntax is no longer visible in emitter code; must consult `backends.yaml`
3. **Validation overhead**: Must validate backend config at emission time; missing system devices become runtime errors rather than compile-time guarantees

### Neutral

1. **No AST/IR changes**: System devices are emission-only; they do not flow through AST → NFIR → IFIR pipeline
2. **Migration effort**: Since we're still in MVP, no backward compatibility constraints; clean refactor is straightforward
3. **Device backends unchanged**: Regular device backends remain inline in ASDL files; only structural elements move to backend config

---

## Alternatives Considered

### Alternative 1: Hardcoded fallbacks with backend overrides

Keep default templates in the emitter code; allow backends to override via config.

**Rejected because**: Partial hardcoding defeats the extensibility goal; still ties emitter to ngspice-like assumptions.

### Alternative 2: Single `__subckt__` device with properties

Define one system device with boolean properties to control commenting, port rendering, etc.

**Rejected because**: Mixing top/non-top logic into a single template makes backend config harder to read and validate.

### Alternative 3: Emitter subclasses per backend

Create `NgspiceEmitter`, `SpectreEmitter`, etc., each with custom logic.

**Rejected because**: Code duplication; harder to maintain shared template rendering logic; doesn't leverage existing template system.

---

## Implementation Notes

- System device names are reserved; AST parser should reject regular devices with `__` prefix
- Missing required system devices should emit diagnostic code `MISSING_BACKEND` (already exists)
- Template placeholder validation should apply to system devices (same as device backends)
- Whitespace collapsing for empty `{ports}` should apply to system devices

---

## References

- Contract decision log: 2026-01-03
- Related: T-046 (individual param placeholders)
- Supersedes: Inline ngspice syntax in `src/asdl/emit/ngspice.py`
