# Spec - ASDL View-Decorated Module Symbols v0

## Purpose
Define how ASDL represents multiple implementation views for a single logical
cell using decorated module symbols, without relying on file-name heuristics.

---

## Scope (v0)
- Module symbol grammar for view-decorated names.
- Logical identity model (`cell` vs `view` token).
- Netlist emission surface rule for mixed-view realizations.
- Validation constraints for malformed decorated symbols.

Out of scope (deferred):
- CLI flags and profile-selection UX.
- Cross-view interface compatibility checks.

---

## Module symbol grammar

`module_symbol` is one of:
- `cell`
- `cell@view`

Where:
- `cell` matches `[A-Za-z_][A-Za-z0-9_]*`
- `view` matches `[A-Za-z_][A-Za-z0-9_]*`

Invalid forms:
- `@view`
- `cell@`
- `cell@view@extra`

---

## Identity model
- Logical cell identity is `cell`.
- `view` is a selectable implementation token for that cell.
- Undecorated `cell` is the default realization token.

Examples:
- `ota_nmos` (canonical/default)
- `ota_nmos@behav`
- `ota_nmos@cascode`
- `ota_nmos@behav_lite`

---

## Emission surface
- Emission is realization-based: one emitted subckt/module per resolved
  `(cell, view)` used by the design.
- Default/undecorated realization emits as `cell`.
- Non-default realization emits as `cell_<view>` (deterministic, sanitized).
- Internal `@view` tokens are not emitted directly in simulator-facing names.
- This enables mixed-view subtree substitution inside a single emitted netlist.

---

## Validation requirements
- Parser/schema validation must accept both `cell` and `cell@view`.
- Validation must reject malformed decorated symbols listed above.
- Diagnostic messages should identify whether failure is in `cell` token, `view`
  token, or `@` usage cardinality.

---

## Notes
- View selection/binding resolution is defined in
  `docs/specs/spec_asdl_view_config.md`.
