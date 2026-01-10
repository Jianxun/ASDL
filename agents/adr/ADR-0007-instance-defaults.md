Title: ADR-0007: Instance Defaults Replace Inline Bindings
Status: Accepted

## Context
Inline pin bindings were introduced as a secondary connectivity source, but they
increase surface complexity and can lead to brittle authoring. We want a simpler
mechanism that reduces boilerplate while keeping connectivity explicit and
deterministic.

## Decision
Add module-level `instance_defaults` to define default endpoint bindings per
instance **reference** (device/module symbol). Inline pin bindings are removed
from the authoring surface.

Shape (module-local):
```yaml
instance_defaults:
  <ref>:
    bindings:
      <port>: <net>
```

Semantics:
- Defaults apply to every instance whose `ref` matches `<ref>`.
- Defaults contribute endpoint bindings to nets (same as `nets:` entries).
- Explicit bindings in `nets` override defaults for the same endpoint.
- If an explicit binding overrides a default, emit a warning unless the
  endpoint token uses `!` prefix (e.g., `!inst.pin`) to suppress the warning.
- If the explicit binding connects to the same net as the default, no warning.
- Defaults may introduce nets; `$`-prefixed nets introduced by defaults create
  ports.
- Port order is:
  1) `$` nets declared in `nets` (source order),
  2) `$` nets first-seen from `instance_defaults` (module order of defaults,
     then binding order within each default entry).

## Consequences
- Inline pin-binding syntax is removed from specs and future implementation.
- Connectivity authoring uses `nets` + `instance_defaults` only.
- Diagnostics must report override warnings (with `!` suppression).

## Alternatives
- Keep inline bindings and add defaults alongside them. Rejected: too many
  binding sources and higher ambiguity.
