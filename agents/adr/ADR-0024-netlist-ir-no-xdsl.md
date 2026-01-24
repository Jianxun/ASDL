ADR-0024: Replace IFIR with NetlistIR dataclass model (remove xDSL)

Status: Accepted

## Context
The refactor goal is a simplified, dataclass-based pipeline without xDSL.
IFIR is currently an xDSL dialect used as an emission-ready projection. Even
with thorough AtomizedGraph validation, emission still needs a normalized,
backend-focused representation plus verification. Keeping IFIR would retain
xDSL in the refactor path, which conflicts with the goal to remove xDSL
completely.

## Decision
- Introduce a dataclass-based emission model named `NetlistIR` as the canonical
  emission-ready representation.
- Replace AtomizedGraph -> IFIR lowering with AtomizedGraph -> NetlistIR
  lowering.
- Migrate IFIR verification tooling to stateless validators that operate on
  NetlistIR.
- Refactor emission to consume NetlistIR directly.
- Remove xDSL usage from the refactor pipeline; xDSL dialects (GraphIR/IFIR)
  become legacy-only until fully retired.

## Consequences
- New NetlistIR data structures, lowering, and verifiers must be defined and
  covered by tests.
- CLI and emit APIs must be updated to accept NetlistIR; adapters for legacy
  IFIR (if temporarily retained) must be explicit and isolated.
- Diagnostics codes and docs must be updated to reflect the NetlistIR pathway.

## Alternatives
- Keep IFIR as the emission IR: rejected because it preserves xDSL in the
  refactor pipeline and complicates the dataclass-only goal.
- Maintain dual IFIR/NetlistIR paths long-term: rejected due to verification
  and maintenance duplication; any overlap must be temporary during migration.
