# T-011 — Parser + Locatable Diagnostics

## Goal
Implement ruamel-based YAML parsing, LocationIndex, and diagnostics mapping for Pydantic validation.

## References
- `agents/specs/spec_ast.md`

## Notes
- Parse with ruamel for line/col, then convert to plain dict for Pydantic.
- Map `ValidationError.errors()` `loc` paths to locations via LocationIndex.
- Keep parser API `parse_file`/`parse_string` returning AST + diagnostics.

## File hints
- `src/asdl/parser/`
- `src/asdl/diagnostics.py`
- `src/asdl/ast/` (Locatable or helpers)
- `tests/unit_tests/parser_v2/`
