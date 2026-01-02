# T-027 - ASDL_NFIR MVP Dialect + Conversion

## Goal
Implement the MVP ASDL_NFIR dialect and AST->NFIR conversion per `docs/specs_mvp/spec_asdl_nfir_mvp.md`.

## DoD
- Dialect ops/attrs implemented with verifiers where specified.
- AST->NFIR conversion parses instance expr into `ref` + `params` and extracts `port_order` from `$` nets.
- Devices/backends are carried 1:1 into NFIR.
- Unit tests cover dialect printing/parsing and conversion outputs.

## Files likely touched
- `src/asdl/ir/`
- `src/asdl/ast/`
- `tests/unit_tests/ir/`
- `tests/unit_tests/parser/`

## Verify
- `pytest tests/unit_tests/ir`
- `pytest tests/unit_tests/parser`
