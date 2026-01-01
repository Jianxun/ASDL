# T-024 — ASDL_NLIR Dialect + Lowering

## Goal
Implement ASDL_NLIR dialect (`asdl_nlir` with `elab_state`) and lower ASDL_CIR into NLIR-U (NLIR-E is identity in MVP).

## References
- `docs/specs/spec_asdl_nlir.md`
- `docs/specs/spec_asdl_cir.md`

## Notes
- MVP assumes explicit names only; metadata intentionally minimal.
- ASDL_NLIR_U/E are distinguished by `elab_state` in the same dialect.
- Preserve `port_order` through CIR → NLIR.

## File hints
- `src/asdl/ir/xdsl_dialect/`
- `src/asdl/ir/converter.py`
- `tests/unit_tests/ir/`

## Verify
- `pytest tests/unit_tests/ir` (ensure `elab_state` is required and consistent)
