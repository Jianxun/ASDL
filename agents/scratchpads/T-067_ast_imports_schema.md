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
- [x] Add AST/parser tests for valid/invalid imports.
- [x] Update AST models + parser validation/diagnostics for imports.
- [x] Document `imports` in `spec_ast`.

## Progress log
- 2026-01-09: Added AST/parser tests for import cases.
- 2026-01-09: Implemented imports schema + parser diagnostics; updated spec.
- 2026-01-09: Verified AST/parser tests.

## Patch summary
- Added imports field to AST models and export surface.
- Parser now detects duplicate import namespaces and validates namespace/path types with AST-011/AST-013 diagnostics.
- Documented top-level `imports` in `docs/specs/spec_ast.md`.

## Verification
- `./venv/bin/pytest tests/unit_tests/ast tests/unit_tests/parser -v`

## Status request
- None.

## Blockers / Questions
- None.
