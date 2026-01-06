# T-061 AST Imports Schema

## Task summary
- DoD: Extend the AST schema to allow a top-level `imports: Dict[str, str]` mapping (namespace -> path) per `docs/specs/spec_asdl_import.md`; update Pydantic models, parser validation/diagnostics, and `scripts/generate_schema.py` output. Update `docs/specs/spec_ast.md` to include `imports` (keep MVP spec unchanged). Add parser/AST tests for valid and invalid `imports` (bad namespace, duplicate key, invalid type). Enforce that documents define at least one module or device (import-only files are invalid).
- Verify: `pytest tests/unit_tests/parser -v && pytest tests/unit_tests/ast -v`

## Read
- `src/asdl/ast/models.py`
- `src/asdl/ast/__init__.py`
- `src/asdl/ast/parser.py`
- `src/asdl/ast/location.py`
- `docs/specs/spec_ast.md`
- `docs/specs/spec_asdl_import.md`
- `scripts/generate_schema.py`
- `tests/unit_tests/parser/test_parser.py`
- `tests/unit_tests/ast/test_models.py`

## Plan
- Add typed `imports` support in `AsdlDocument` with namespace validation.
- Update parser diagnostics via Pydantic errors for invalid namespaces/paths.
- Document `imports` in `docs/specs/spec_ast.md` (leave MVP spec unchanged).
- Add parser/AST tests for valid imports, bad namespace, bad path type, duplicate key, and import-only files.

## Progress log
- Initialized scratchpad.
- Reviewed import/spec AST requirements and parser location handling.
- Added imports schema/types, updated spec, and expanded parser/AST tests.
- Ran parser and AST unit tests.
- Pushed branch and opened PR https://github.com/Jianxun/ASDL/pull/52.

## Patch summary
- `src/asdl/ast/models.py`: added typed imports mapping with namespace pattern validation.
- `src/asdl/ast/__init__.py`: exported imports-related types.
- `docs/specs/spec_ast.md`: documented `imports` field and requirements.
- `tests/unit_tests/parser/test_parser.py`: added imports parser coverage (valid/invalid/duplicate/import-only).
- `tests/unit_tests/ast/test_models.py`: added imports schema validation coverage.

## Verification
- `./venv/bin/pytest tests/unit_tests/parser -v` (pass)
- `./venv/bin/pytest tests/unit_tests/ast -v` (pass)

## Status request
- Ready for Review.

## Blockers / Questions
- None.

## Next steps
- Await Reviewer feedback.
