# Spec S — ASDL Compiler Stack v0

## Purpose
Define the canonical compiler stack, IR IDs, and MVP scope. This document is the
source of truth for stage boundaries and naming.

---

## IR IDs (formal)
- **ASDL_A**: Tier-1 authoring AST (net-first YAML surface).
- **ASDL_NFIR**: Net-First IR (xDSL dialect `asdl_nfir`).
- **ASDL_IFIR**: Instance-First IR (xDSL dialect `asdl_ifir`).

---

## Pipeline (canonical)
Tier-1 YAML → ASDL_A → ASDL_NFIR → (NFIR verify) → ASDL_IFIR → (IFIR verify) → pattern elaboration → backend emission.

---

## MVP scope (skeleton stack)
- Pattern tokens are preserved through NFIR/IFIR; elaboration happens just before emission.
- No import system (deferred).
- Exports block is optional sugar (deferred).
- Ports are inferred only from `$`-prefixed net keys in `nets:`.
- Port order is the YAML source order of `$` nets.
- Port order is a first-class attribute and must be propagated through NFIR/IFIR into emission.

---

## Pattern semantics (post-MVP)
- Pattern tokens are preserved as raw strings; no basename decomposition.
- **Pattern elaboration** expands all tokens before emission.

---

## View system (deferred)
View selection is not part of the current stack and will be revisited later.
