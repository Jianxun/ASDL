# T-043 Endpoint Lists (Lists Only)

## Goal
Implement list-only endpoint authoring once delimiter policy is adopted.

## Notes
- Disallow string endpoint lists; require YAML lists of strings.
- Update parser validation, AST schema, and converters.
- Improve diagnostics to guide users toward list authoring.

## Files
- src/asdl/ast/models.py
- src/asdl/ast/parser.py
- src/asdl/ir/converters/ast_to_nfir.py
- tests/unit_tests/parser/
- tests/unit_tests/ir/
