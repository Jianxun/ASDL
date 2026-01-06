# T-067 AST imports schema

## Task summary
- **DoD**: Add top-level `imports: Dict[str, str]` to AST models and parser per `docs/specs/spec_asdl_import.md`. Validate namespace syntax, reject non-string paths (`AST-011`), detect duplicate namespaces (`AST-013`), and enforce non-empty documents (no import-only files). Update `docs/specs/spec_ast.md` and add AST/parser tests.
- **Verify**: `pytest tests/unit_tests/ast tests/unit_tests/parser -v`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_import.md`
- `docs/specs/spec_ast.md`
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `tests/unit_tests/ast/test_models.py`
- `tests/unit_tests/parser/test_parser.py`

## Plan
1. Update AST models to include `imports` with validation hooks for namespaces and path types.
2. Wire parser support + diagnostics for duplicate namespaces and import-only documents.
3. Add targeted tests for valid/invalid imports and run the listed pytest command.

## Progress log
- Not started yet.

## Status request
- None.

## Blockers / Questions
- None.

