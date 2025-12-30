# T-012 — xDSL Dialect + AST→IR

## Goal
Implement the `asdl.ir` xDSL dialect and AST→IR converter per `spec_asdl_ir.md`.

## References
- `agents/specs/spec_asdl_ir.md`
- `agents/specs/spec_ast.md`

## Notes
- Implement ops/attrs and verifiers for v0 constraints.
- Converter emits `asdl.design/module/view/...` and normalizes `nom` → `nominal` before IR emission.
- Tests should skip if xdsl is not installed.

## File hints
- `src/asdl/ir/xdsl_dialect/`
- `src/asdl/ir/converter.py`
- `tests/unit_tests/ir/`
