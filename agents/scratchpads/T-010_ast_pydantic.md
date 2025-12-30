# T-010 — AST Pydantic v2

## Goal
Implement Pydantic v2 AST models aligned with `agents/specs/spec_ast.md`.

## References
- `agents/specs/spec_ast.md`

## Notes
- Use discriminated unions keyed by `kind` for `ViewDecl`.
- Enforce AST hard requirements in validators (non-empty templates, dummy name/kind coupling).
- Keep loc metadata out of the schema (PrivateAttr or post-attach).

## File hints
- `src/asdl/ast/`
- `tests/unit_tests/ast/`
