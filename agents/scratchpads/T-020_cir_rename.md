# T-020 — Core IR Dialect Rename (ASDL_CIR)

## Goal
Rename the core xDSL dialect to `asdl_cir` in code/tests and align converter usage with ASDL_CIR naming.

## References
- `docs/specs/spec_compiler_stack.md`
- `docs/specs/spec_asdl_cir.md`

## Notes
- Keep semantics identical; only rename ops/attrs and textual IR names.

## File hints
- `src/asdl/ir/xdsl_dialect/`
- `src/asdl/ir/converter.py`
- `tests/unit_tests/ir/`
