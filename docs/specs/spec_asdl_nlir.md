# Spec D — ASDL_NLIR (Netlist IR) v0

## Purpose
ASDL_NLIR is a formal netlist IR for emission and as an entry point for third-
party flows. It exists in two forms:
- **ASDL_NLIR_U**: unelaborated (pattern domains preserved).
- **ASDL_NLIR_E**: elaborated (all names/endpoints expanded).

---

## MVP constraints
- Only explicit names (no pattern domains).
- ASDL_NLIR_U and ASDL_NLIR_E are identical in MVP.
- Metadata fields are intentionally minimal; they will be refined as the stack
  is exercised.

---

## Draft ops (xDSL dialect `asdl_nlir`)
This is a placeholder skeleton for MVP planning. Details may change.

### `asdl_nlir.design`
**Role**: top-level container for netlist units.

### `asdl_nlir.subckt`
**Role**: explicit subcircuit definition (ports + instances).

### `asdl_nlir.instance`
**Role**: instance statement with resolved connectivity.

---

## Invariants (v0)
- ASDL_NLIR_E has **fully elaborated** names and endpoints.
- ASDL_NLIR_U may retain pattern domains but must be structurally valid.
