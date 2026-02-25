# Spec - ASDL View-Decorated Module Symbols v0

## Purpose
Define how ASDL represents multiple implementation views for a single logical
cell using decorated module symbols, without relying on file-name heuristics.

---

## Scope (v0)
- Module symbol grammar for view-decorated names.
- Logical identity model (`cell` vs `view` token).
- Netlist emission surface rule for mixed-view realizations and reachable-only
  emission from the final resolved top.
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
- `cell@default` is allowed as an explicit authored alias and normalizes to the
  default realization at emission.

Examples:
- `ota_nmos` (canonical/default)
- `ota_nmos@behav`
- `ota_nmos@cascode`
- `ota_nmos@behav_lite`

---

## Emission surface
- Emission is realization-based and rooted at the final resolved top module.
- Emit only modules reachable from that final top via transitive instance
  references.
- Default/undecorated realization emits as `cell`.
- `cell@default` also emits as `cell`.
- Non-default realization emits as `cell_<view>` (deterministic, sanitized).
- Internal `@view` tokens are not emitted directly in simulator-facing names.
- This enables mixed-view subtree substitution inside a single emitted netlist.
- Path-scoped view overrides may produce multiple realized variants of the same
  logical cell; all reachable realized variants are emitted.
- Collision disambiguation policy (v0):
  - emit modules in deterministic traversal order from lowering/emission
  - allocate simulator-facing names incrementally from a global used-name set
  - first occurrence uses base realization name (`cell` or `cell_<view>`)
  - later collisions append ordinal suffixes `__2`, `__3`, ... until unique
  - this rule also covers collisions where `cell_<view>` matches an existing
    undecorated module name
- Emitters SHOULD report collision renames as warnings and provide a deterministic
  logical-to-emitted mapping artifact for inspection/debug.

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
- Hierarchy instance indexing should follow the shared traversal contract in
  `docs/specs/spec_hierarchy_traversal.md` with module-only inclusion.
