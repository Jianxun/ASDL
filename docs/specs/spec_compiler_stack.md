# Spec — ASDL Compiler Stack v0

## Purpose
Define the canonical compiler stack, IR IDs, and MVP scope. This document is the
source of truth for stage boundaries and naming.

---

## IR IDs (formal)
- **ASDL_A**: Tier-1 authoring AST (net-first YAML surface).
- **ASDL_NFIR**: Net-First IR (xDSL dialect `asdl_nfir`).
- **ASDL_GRAPHIR**: GraphIR semantic core (xDSL dialect `graphir`).
- **ASDL_IFIR**: Instance-First IR (xDSL dialect `asdl_ifir`).

---

## Pipeline (canonical)
Tier-1 YAML → ASDL_A → import resolution (ProgramDB + NameEnv) → ASDL_NFIR →
(NFIR verify) → pattern expansion (metadata + atoms) → ASDL_GRAPHIR →
(GraphIR verify) → GraphIR->IFIR projection → backend emission.
See `docs/specs/spec_pipeline.md` for entrypoint and pass ordering.

---

## MVP scope (skeleton stack)
- Pattern tokens are expanded into GraphIR atoms with bundle metadata; GraphIR
  is the semantic source of truth.
- The pipeline entrypoint returns GraphIR; IFIR is a projection step used for
  emission.
- Imports are resolved before AST->NFIR; symbol identity is `(file_id, name)` and `file_id`
  is propagated through NFIR/IFIR. Entry `file_id` is exposed to netlist templates.
- Exports block is optional sugar (deferred).
- Ports are inferred only from `$`-prefixed net keys in `nets:`.
- Port order is the YAML source order of `$` nets.
- Port order is a first-class attribute and must be propagated through NFIR/IFIR into emission.

---

## Pattern semantics (post-MVP)
- Pattern expansion runs before GraphIR and yields atomized members plus bundle
  metadata; no pattern inference is performed later.
- Emission consumes IFIR projected from GraphIR and does not require an
  additional elaboration pass.

---

## View system (deferred)
View selection is not part of the current stack and will be revisited later.
