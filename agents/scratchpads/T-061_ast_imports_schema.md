# T-061 AST Imports Schema

## Task summary
- DoD: Extend the AST schema to allow a top-level `imports: Dict[str, str]` mapping (namespace -> path) per `docs/specs/spec_asdl_import.md`; update Pydantic models, parser validation/diagnostics, and `scripts/generate_schema.py` output. Update `docs/specs/spec_ast.md` to include `imports` (keep MVP spec unchanged). Add parser/AST tests for valid and invalid `imports` (bad namespace, duplicate key, invalid type).
- Verify: `pytest tests/unit_tests/parser -v && pytest tests/unit_tests/ast -v`

## Read
- `src/asdl/ast/models.py`
- `src/asdl/ast/__init__.py`
- `src/asdl/ast/parser.py`
- `docs/specs/spec_ast.md`
- `docs/specs/spec_asdl_import.md`
- `scripts/generate_schema.py`
- `tests/unit_tests/parser/`
- `tests/unit_tests/ast/`

## Plan
- Add an `imports: Optional[Dict[str, str]]` field to `AsdlDocument`.
- Validate namespace key format and string values; emit diagnostics for invalid keys/types.
- Update spec_ast to document `imports`; keep MVP spec unchanged.
- Add parser/AST tests for valid imports, invalid namespace keys, and non-string paths.
- Regenerate schema artifacts.

## Progress log
- Added imports field + namespace validation in AST models and exports in `asdl.ast`.
- Updated spec_ast and regenerated schema artifacts.
- Added parser/AST tests for imports and import-only rule; ran unit tests.
- Opened PR: https://github.com/Jianxun/ASDL/pull/51

## Patch summary
- `src/asdl/ast/models.py`: add imports field and namespace validation.
- `src/asdl/ast/__init__.py`: export `ImportsBlock`.
- `docs/specs/spec_ast.md`: document `imports` in AST spec.
- `legacy_doc/schema/schema.json`: regenerate schema output.
- `legacy_doc/schema/schema.txt`: regenerate schema output.
- `tests/unit_tests/ast/test_models.py`: add imports and import-only validation tests.
- `tests/unit_tests/parser/test_parser.py`: add parser tests for imports handling.

## Verification
- `./venv/bin/pytest tests/unit_tests/parser -v`
- `./venv/bin/pytest tests/unit_tests/ast -v`

## Status request
- Ready for review.

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
