# T-294 - Enforce decorated module symbol grammar in AST parse/schema

## Goal
Validate module symbols against `cell` / `cell@view` grammar during parsing/schema validation.

## Notes for Executor
- Cover both module declaration names and instance references.
- Reject malformed forms: `@view`, `cell@`, `cell@view@extra`.
- Emit parser diagnostics rather than raw exceptions.

## Verify
- `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/parser/test_parser.py -k "view or decorated or module symbol" -v`
