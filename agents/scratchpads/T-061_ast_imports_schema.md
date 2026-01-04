# T-061 AST Imports Schema

## Task summary
- DoD: Extend the AST schema to allow a top-level `imports: Dict[str, str]` mapping (namespace -> path) per `docs/specs/spec_asdl_import.md`; update Pydantic models, parser validation/diagnostics, and `scripts/generate_schema.py` output. Update `docs/specs/spec_ast.md` to include `imports` (keep MVP spec unchanged). Add parser/AST tests for valid and invalid `imports` (bad namespace, duplicate key, invalid type).
- Verify: `pytest tests/unit_tests/parser -v && pytest tests/unit_tests/ast -v`

## Read
- `src/asdl/ast/models.py`
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
- Add tests for valid imports, invalid namespace keys, and non-string paths.

## Progress log
- Initialized scratchpad.

## Patch summary
- TBD.

## Verification
- TBD.

## Blockers / Questions
- None.

## Next steps
- Implement schema changes and expand parser/AST tests.
