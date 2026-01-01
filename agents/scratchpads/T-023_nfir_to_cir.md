# T-023 — ASDL_NFIR → ASDL_CIR Lowering

## Goal
Lower net-first IR into canonical ASDL_CIR by inverting nets into named-only instance conns.

## References
- `docs/specs/spec_asdl_nfir.md`
- `docs/specs/spec_asdl_cir.md`

## Notes
- Ports derived from `$` nets with source order.

## File hints
- `src/asdl/ir/converter.py`
- `tests/unit_tests/ir/`
