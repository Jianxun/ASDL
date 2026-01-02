# T-028 - ASDL_IFIR MVP Dialect + Conversion

## Goal
Implement the MVP ASDL_IFIR dialect and NFIR->IFIR conversion per `docs/specs_mvp/spec_asdl_ifir_mvp.md`.

## DoD
- Dialect ops/attrs implemented with verifiers where specified.
- NFIR->IFIR conversion inverts nets into named conns and emits explicit nets.
- `port_order` is preserved.
- Unit tests cover dialect printing/parsing and conversion outputs.

## Files likely touched
- `src/asdl/ir/`
- `tests/unit_tests/ir/`

## Verify
- `pytest tests/unit_tests/ir`
