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
This is a placeholder skeleton for MVP planning. Details may change. Both
ASDL_NLIR_U and ASDL_NLIR_E use this dialect and are distinguished by an
explicit elaboration state attribute.

### `asdl_nlir.design`
**Role**: top-level container for netlist units.
**Attributes**
- `elab_state: StringAttr` (`"u"` or `"e"`)

### `asdl_nlir.subckt`
**Role**: explicit subcircuit definition (ports + instances).
**Attributes**
- `elab_state: StringAttr` (`"u"` or `"e"`) (must match parent)

### `asdl_nlir.instance`
**Role**: instance statement with resolved connectivity.

---

## Invariants (v0)
- ASDL_NLIR_E has **fully elaborated** names and endpoints.
- ASDL_NLIR_U may retain pattern domains but must be structurally valid.
- All ops in a design share the same `elab_state`.
