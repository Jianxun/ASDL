# T-012 — xDSL Dialect + AST→IR

## Goal
Implement the `asdl_cir` xDSL dialect and AST→IR converter per `docs/specs/spec_asdl_cir.md`.

## References
- `docs/specs/spec_asdl_cir.md`
- `docs/specs/spec_ast.md`

## Notes
- Implement ops/attrs and verifiers for v0 constraints.
- Converter emits `asdl.design/module/view/...` and normalizes `nom` → `nominal` before IR emission.
- Tests should skip if xdsl is not installed.

## File hints
- `src/asdl/ir/xdsl_dialect/`
- `src/asdl/ir/converter.py`
- `tests/unit_tests/ir/`
