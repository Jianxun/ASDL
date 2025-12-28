# ADR-0001: Reserved view names and kinds

- Status: Proposed
- Date: 2025-12-28

## Context
- The ASDL refactor makes views first-class; selection operates on `(module, view)`.
- We need minimal, enforceable reserves for names and kinds while keeping authors free to define additional views.
- PEX should be modeled as an external netlist specialization, not a separate primitive.

## Decision
- Reserved view names: `nominal` (canonical default; `nom` alias accepted) and `dummy`. All other view names are user-defined.
- Reserved view kinds: `subckt`, `subckt_ref`, `primitive`, `dummy`.
  - `pex` is a specialization of `subckt_ref` (external netlist) with explicit port→pin mapping.
- Multiple views may coexist on a module; exclusivity is resolved during view selection, not at schema level.

## Consequences
- Schema and pydantic models must encode views with:
  - name (free string, except the two reserved)
  - kind enum restricted to {subckt, subckt_ref, primitive, dummy}
  - `subckt_ref` covers PEX/external netlists; no separate `pex` kind.
- View selection/config logic must treat `nominal` as the default, recognize `dummy`, and allow user-defined names otherwise.
- Documentation and scratchpads must align to this reserved set; earlier broader reserved lists are superseded.

## Alternatives
- Broader reserved vocabulary (e.g., behav/pex/blackbox) — rejected to reduce rigidity and keep user-defined views flexible.
- No reserved names — rejected; `nominal` default and `dummy` blackout need stable handling across tools.

