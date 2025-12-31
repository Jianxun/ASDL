# T-011 — Parser + Locatable Diagnostics

## Task summary (DoD + verify)
- DoD: Build YAML parser using ruamel -> plain dict -> Pydantic validation; implement LocationIndex to map YAML paths to Locatable; map Pydantic ValidationError into Diagnostic with correct locations; update parser API (parse_file/parse_string) to return AST + diagnostics; add location-mapping tests.
- Verify: `pytest tests/unit_tests/parser`

## Read
- `docs/specs/spec_ast.md`
- `src/asdl/ast/models.py`
- `src/asdl/diagnostics/core.py`
- `legacy/src/asdl/parser/asdl_parser.py` (legacy parser; will not reuse for implementation)
- `legacy/src/asdl/parser/core/locatable_builder.py`

## Plan
1. Create a new parser module (no legacy parser reuse) that loads YAML via ruamel, converts to plain dict/list, and validates with `AsdlDocument.model_validate`.
2. Implement `LocationIndex` that walks ruamel `CommentedMap`/`CommentedSeq` and maps YAML paths to `Locatable` (1-based line/col), with parent fallback for missing-field errors.
3. Convert `ValidationError.errors()` into `Diagnostic` entries, using LocationIndex path lookup and reasonable defaults when missing.
4. Walk the validated AST and attach `_loc` using `set_loc` from the LocationIndex.
5. Update `parse_file`/`parse_string` API and adjust call sites to return `(AsdlDocument | None, diagnostics)`.
6. Add `tests/unit_tests/parser` to cover YAML syntax error, invalid root type, missing required field, nested field error, and location mapping.

## Progress log
- 2025-12-30: Task assigned (T-011). Branch creation failed due to `.git` permission error; no code changes yet.
- 2025-12-30: User clarified this is a breaking change; no backward compatibility required.
- 2025-12-30: Created fresh `feature/T-011-parser-locatable` branch; blocker cleared.
- 2025-12-30: Added LocationIndex/Locatable, parser entrypoints, diagnostics mapping, and parser tests; ran pytest.
- 2025-12-30: Pushed branch and opened PR https://github.com/Jianxun/ASDL/pull/20.
- 2025-12-30: Addressed review notes (file-not-found diagnostics + exclusive end spans); reran parser tests.
- 2025-12-30: Added required no-span notes for diagnostics without locations; reran parser tests.

## Patch summary
- `src/asdl/ast/location.py`: implement Locatable + LocationIndex with YAML path mapping and plain-data conversion.
- `src/asdl/ast/parser.py`: new ruamel → Pydantic parser with validation diagnostics and location attachment.
- `src/asdl/ast/__init__.py`: export parser and location helpers.
- `src/asdl/__init__.py`: re-export parser and location helpers at top level.
- `tests/unit_tests/parser/test_parser.py`: coverage for parsing success, root errors, and location mapping.

## Verification
- `./venv/bin/pytest tests/unit_tests/parser`

## Blockers / Questions
- None.

## Next steps
1. Await review on PR https://github.com/Jianxun/ASDL/pull/20.
