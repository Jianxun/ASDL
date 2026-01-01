# Spec S — ASDL Compiler Stack v0

## Purpose
Define the canonical compiler stack, IR IDs, and MVP scope. This document is the
source of truth for stage boundaries and naming.

---

## IR IDs (formal)
- **ASDL_A**: Tier-1 authoring AST (net-first YAML surface).
- **ASDL_NFIR**: Net-First IR (xDSL dialect `asdl_nfir`).
- **ASDL_CIR**: Core IR (xDSL dialect `asdl_cir`).
- **ASDL_NLIR_U**: Netlist IR, unelaborated (xDSL dialect `asdl_nlir` with `elab_state=u`).
- **ASDL_NLIR_E**: Netlist IR, elaborated (xDSL dialect `asdl_nlir` with `elab_state=e`).

---

## Pipeline (canonical)
Tier-1 YAML → ASDL_A → ASDL_NFIR → ASDL_CIR → passes (MVP: minimal/no-op) → ASDL_NLIR_U → ASDL_NLIR_E → backend emission.

---

## MVP scope (skeleton stack)
- Only explicit instances and nets (no pattern/domain sugar).
- No import system.
- No exports block.
- View selection and compatibility metadata are deferred.
- Ports are inferred only from `$`-prefixed net keys in `nets:`.
- Port order is the YAML source order of `$` nets.
- Port order is a first-class attribute and must be propagated through NFIR/CIR/NLIR into emission.
- ASDL_NLIR_U and ASDL_NLIR_E share the `asdl_nlir` dialect; elaboration state is explicit.

---

## Pattern semantics (post-MVP)
- **Domain wildcard sugar** resolves during ASDL_A → ASDL_NFIR.
- **Pattern elaboration** expands all domains before ASDL_NLIR_E.
- Names are represented as **basename + optional pattern domain** until elaboration.

---

## View system (deferred)
View selection is not part of the MVP stack. It will be introduced as a separate
flow layer (potentially a sidecar manifest) that operates on ASDL_CIR or later.
