# ADR-0003: View selection pass and validation

- Status: Proposed
- Date: 2025-12-28

## Context
- Modules may define multiple views (user-defined names plus reserved `nominal` and `dummy`).
- Reserved view kinds are defined in ADR-0001 (`subckt`, `subckt_ref`, `primitive`, `dummy`).
- Selection must be deterministic and compatible with Cadence-like view-order/config flows.

## Decision
- Implement a dedicated SelectView compiler pass that:
  - Runs after config overlay and view_order resolution.
  - Validates **all views** as if they will be used (no deferred validation).
  - Produces a resolved mapping `(module, selected_view)` for downstream lowering.
  - Errors if a required view is missing, malformed, or fails validation.
- Multiple views may coexist; exclusivity is enforced by selection, not by schema.
- Default behavior selects `nominal` when unspecified; `dummy` reserved for blackout use.

## Consequences
- The pass must surface diagnostics for missing/invalid views before lowering.
- Downstream passes can assume exactly one validated view per module instance.
- Schema/pydantic shapes must carry enough metadata for the pass to validate views by kind.

## Alternatives
- Validate views only when selected — rejected; would allow latent errors and non-determinism.
- Enforce single-view-at-schema — rejected; conflicts with multi-view authoring model.

