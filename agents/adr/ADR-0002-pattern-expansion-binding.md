# ADR-0002: Pattern expansion and binding semantics

- Status: Proposed
- Date: 2025-12-28

## Context
- ASDL supports pattern-based identifiers for ports, nets, and instances.
- Deterministic expansion and binding are required for validation and compiler passes.
- Implicit shape inference or positional binding would create ambiguity and tooling fragility.

## Decision
- Expansion always yields a flat, ordered list of scalars; order is semantic.
- Operators apply left-to-right, duplicating the entire list at each step; suffix-only.
- Tuples concatenate expanded lists (no zipping/broadcasting across tuple elements).
- Binding is **named-only**; positional binding is forbidden.
- Binding length rule: RHS length must be 1 (scalar broadcast) or equal to group size; otherwise error.
- Broadcast is allowed only for scalar RHS; patterns on RHS require explicit repetition (e.g., `repeat(expr, N)`).
- Error on identifier collisions after expansion.
- Lint errors for malformed patterns/unquoted flow-style patterns; fail fast on unmatched delimiters/ranges.

## Consequences
- Compiler must implement a deterministic expander with left-to-right duplication semantics.
- Verifiers must enforce binding length rules, detect collisions, and reject implicit reshaping/zipping.
- Linter must warn/fail on malformed or unquoted patterns in flow style.
- Canonical ordering must be preserved through lowering to maintain determinism.

## Alternatives
- Allow positional binding or implicit broadcasts — rejected due to ambiguity and brittle intent.
- Permit multi-dimensional structures — rejected; flat lists are simpler and deterministic.

