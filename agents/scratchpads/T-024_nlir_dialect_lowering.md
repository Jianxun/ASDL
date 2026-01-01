# T-024 — ASDL_NLIR Dialect + Lowering

## Goal
Implement ASDL_NLIR (U/E) dialect(s) and lower ASDL_CIR into NLIR-U (NLIR-E is identity in MVP).

## References
- `docs/specs/spec_asdl_nlir.md`
- `docs/specs/spec_asdl_cir.md`

## Notes
- MVP assumes explicit names only; metadata intentionally minimal.

## File hints
- `src/asdl/ir/xdsl_dialect/`
- `src/asdl/ir/converter.py`
- `tests/unit_tests/ir/`
