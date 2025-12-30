# T-015 — Legacy Cleanup

## Goal
Remove legacy dataclass AST/parsing code and update imports/tests to use the new Pydantic AST.

## References
- `agents/specs/spec_ast.md`

## Notes
- Delete or relocate deprecated modules under `src/asdl/data_structures/` and old parser components.
- Update documentation and exports to reference the new AST package.

## File hints
- `src/asdl/data_structures/`
- `src/asdl/parser/`
- `src/asdl/__init__.py`
- `tests/`
