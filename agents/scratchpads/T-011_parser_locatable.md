# T-011 — Parser + Locatable Diagnostics

## Task summary (DoD + verify)
- DoD: Build YAML parser using ruamel -> plain dict -> Pydantic validation; implement LocationIndex to map YAML paths to Locatable; map Pydantic ValidationError into Diagnostic with correct locations; update parser API (parse_file/parse_string) to return AST + diagnostics; add location-mapping tests.
- Verify: `pytest tests/unit_tests/parser_v2`

## Read
- `docs/specs/spec_ast.md`
- `src/asdl/ast/models.py`
- `src/asdl/diagnostics.py`
- `src/asdl/parser/asdl_parser.py` (legacy parser; will not reuse for implementation)

## Plan
1. Create a new parser module (no legacy parser reuse) that loads YAML via ruamel, converts to plain dict/list, and validates with `AsdlDocument.model_validate`.
2. Implement `LocationIndex` that walks ruamel `CommentedMap`/`CommentedSeq` and maps YAML paths to `Locatable` (1-based line/col), with parent fallback for missing-field errors.
3. Convert `ValidationError.errors()` into `Diagnostic` entries, using LocationIndex path lookup and reasonable defaults when missing.
4. Walk the validated AST and attach `_loc` using `set_loc` from the LocationIndex.
5. Update `parse_file`/`parse_string` API and adjust call sites to return `(AsdlDocument | None, diagnostics)`.
6. Add `tests/unit_tests/parser_v2` to cover YAML syntax error, invalid root type, missing required field, nested field error, and location mapping.

## Progress log
- 2025-xx-xx: Task assigned (T-011). Branch creation failed due to `.git` permission error; no code changes yet.
- 2025-xx-xx: User clarified this is a breaking change; no backward compatibility required.

## Patch summary
- None yet.

## Verification
- Not run.

## Blockers / Questions
- Blocked on branch creation: `fatal: cannot lock ref ... Operation not permitted`. Need permissions fixed or branch created by user.

## Next steps
1. Create feature branch `feature/T-011-parser-locatable` (or have user create it).
2. Implement new parser + LocationIndex (no legacy parser reuse).
3. Add parser_v2 tests and run `pytest tests/unit_tests/parser_v2`.
