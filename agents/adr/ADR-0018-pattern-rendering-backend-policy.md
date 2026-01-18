# ADR-0018: Backend Pattern Rendering Policy

Status: Proposed

## Context
ASDL pattern expansion produces atomized names like `Q1`, `Q2`, etc. Some
backends and downstream flows require emitting indexed names with brackets
(e.g., `Q[1]`, `Q[2]`). Because literal names must not include brackets, this
formatting cannot be expressed in authoring syntax and must be applied at
emission time. Pattern semantics are first-class and should remain explicit in
IR to avoid heuristic string rewrites.

## Decision
- Introduce a backend-level rendering policy for pattern-derived names.
- The policy is applied during netlist emission and is driven by pattern
  provenance metadata (pattern origin + parts), not by regex heuristics.
- Numeric pattern parts can be rendered with a configurable index style (e.g.,
  plain suffix `Q1` or bracketed `Q[1]`).
- Emission must not change identity; rendering is presentation-only.
- IFIR will carry pattern provenance metadata and access to the originating
  pattern expressions (e.g., via a pattern expression table) so renderers can
  format numeric parts without re-parsing authoring sources.

## Consequences
- Requires extending backend config schema and emitter logic to honor a pattern
  rendering policy.
- Requires propagating pattern provenance into emission (IFIR or GraphIR
  emission path) to avoid lossy formatting.
- No changes to pattern expansion rules or authoring syntax.

## Alternatives
- Heuristic string rewrites on emitted names: rejected because they lose
  semantics and break for mixed patterns.
- Encode brackets in authoring syntax: rejected due to delimiter conflicts and
  literal-name restrictions.
