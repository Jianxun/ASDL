# ADR-0014: GraphIR as canonical semantic core

Status: Accepted
Date: 2026-01-16

Context
- The MVP pipeline needs a single semantic IR to avoid duplicating verification
  logic across NFIR and IFIR.
- Import-aware compilation requires stable identifiers that do not depend on
  mutable names.
- Graph connectivity must capture modules, instances, nets, and endpoints with
  deterministic port ordering.

Decision
- GraphIR is the canonical semantic core between AST lowering and IFIR
  projection; NFIR remains an optional authoring/roundtrip view.
- The GraphIR dialect defines:
  - `graphir.program` as the root container with optional `entry` and
    `file_order`.
  - `graphir.module` and `graphir.device` with stable `*_id` attributes, `name`,
    `file_id`, and optional metadata.
  - `graphir.net` containing `graphir.endpoint` ops, with endpoints referencing
    instance IDs and port paths.
  - `graphir.instance` with resolved `GraphSymbolRefAttr` (kind + ID) plus the
    raw textual reference.
- Stable IDs use `GraphIdAttr`; instance references use `GraphSymbolRefAttr`.
- `graphir.module` stores ordered ports in `attrs.port_order` (reserved key) and
  verifies net/instance uniqueness and endpoint ownership/uniqueness.

Consequences
- GraphIR is the single source of semantic truth; verifiers and converters
  target GraphIR, and IFIR is a thin projection.
- Import graph assembly and diagnostics use stable IDs rather than name-based
  matching.
- Port ordering is preserved via the explicit `port_order` attribute and list
  ordering in ops.

Alternatives
- Keep NFIR or IFIR as the canonical IR: rejected due to duplicated verification
  logic and emission-specific constraints.
- Use name-only references: rejected because names are not stable across imports
  and refactors.
