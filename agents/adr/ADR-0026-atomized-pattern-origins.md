ADR-0026: Store pattern origins on AtomizedGraph entities

Status: Proposed

## Context
Numeric pattern rendering and other pattern-origin consumers depend on a
consistent origin mapping from expanded atoms back to their source pattern
expressions. The current pipeline registers `pattern_origins` only for
PatternedGraph entities using a tuple `(expr_id, segment_index, token_index)`.
During AtomizedGraph -> NetlistIR lowering, the origin must be reconstructed by
re-expanding the expression and interpreting the third tuple element as an
atom index. This conflates token and atom indices and causes incorrect/missing
origins for most atoms.

## Decision
- Attach pattern-origin metadata directly to AtomizedGraph entities (nets,
  instances, endpoints, and params if needed) with explicit atom indices.
- Populate these origins during atomization, alongside literal name expansion.
- NetlistIR lowering copies atomized origins directly without reconstruction.
- Keep `registries.pattern_origins` scoped to PatternedGraph only; do not
  overload it with atomized IDs.

## Consequences
- AtomizedGraph dataclasses and builders change to carry per-atom origin
  metadata; related dump/verification utilities may need updates.
- NetlistIR lowering becomes simpler and more reliable (no expansion-based
  origin reconstruction).
- Slight memory overhead for storing per-atom origin metadata.

## Alternatives
- Extend `registries.pattern_origins` with atomized IDs: rejected because it
  mixes PatternedGraph and AtomizedGraph namespaces and preserves ambiguous
  tuple semantics.
- Keep NetlistIR reconstruction and search for matching atoms: rejected due to
  ambiguity with duplicates and hidden coupling to expansion logic.
- Redefine the existing origin tuple to mean atom index everywhere: rejected
  because it breaks PatternedGraph token semantics and hides the distinction.
