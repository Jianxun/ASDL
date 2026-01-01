# T-022 — ASDL_NFIR Dialect + AST→NFIR

## Goal
Implement ASDL_NFIR xDSL dialect and convert ASDL_A AST into net-first IR.

## References
- `docs/specs/spec_compiler_stack.md`
- `docs/specs/spec_asdl_nfir.md`

## Notes
- MVP: explicit nets/instances only, explicit endpoints.

## File hints
- `src/asdl/ir/xdsl_dialect/`
- `src/asdl/ir/converter.py`
- `tests/unit_tests/ir/`
