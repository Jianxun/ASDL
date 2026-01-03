# Spec - Netlist Emission (ngspice) v0 (MVP)

## Purpose
Define MVP emission rules from ASDL_IFIR into ngspice-compatible netlists.

---

## MVP scope
- Target backend is ngspice.
- Only named connections (no positional conns).
- Subckt parameters are not supported.
- Device parameters are merged and rendered as `k=v` tokens.

---

## Top selection
- If `design.top` is set, emit that module.
- If `design.top` is absent and only one module exists, emit that module.
- If multiple modules exist and `design.top` is absent, emit an error diagnostic.

---

## Top wrapper handling
- Always emit the top module body.
- Default behavior: comment out the top module's `.subckt` and `.ends` lines.
  - Comment prefix is `*` at column 1.
- `--top-as-subckt`: keep the `.subckt` and `.ends` lines uncommented.

---

## Instance connection ordering
- If instance references a **module**: order nets by the referenced module's
  `port_order`.
- If instance references a **device**: order nets by the device's `ports`.
- Conns are named-only; no positional conns exist in IFIR.

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
- All param values are raw strings in IFIR.
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

## Template contract (devices)
- Each device backend supplies a `template` string.
- Supported placeholders:
  - `{name}` instance name
  - `{ports}` space-joined nets in port order (may be empty)
- `{params}` is deprecated; templates should not rely on it.
- Additional placeholders may be populated from backend `props`.

---

## ngspice module instantiation
- Use `X` instance prefix for module references:
  ```
  X<name> <conns> <subckt_name>
  ```
- Subckt parameters are not supported in MVP.
