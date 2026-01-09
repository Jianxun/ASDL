# T-081 Import path env var expansion

## Objective
Expand `~` and `$VAR`/`${VAR}` in import paths and `ASDL_LIB_PATH` roots, with tests and spec alignment.

## DoD
- Import path resolution expands user home and env vars in `imports` values.
- `ASDL_LIB_PATH` entries expand user home and env vars.
- Malformed or empty expanded paths emit `AST-011` diagnostics.
- Tests cover env expansion for direct import paths and logical paths via `ASDL_LIB_PATH`.
- Import spec references the expansion behavior consistently.

## Files
- src/asdl/imports/resolver.py
- tests/unit_tests/parser/test_import_resolution.py
- docs/specs/spec_asdl_import.md

## Verify
- pytest tests/unit_tests/parser/test_import_resolution.py -v

## Notes
- Use deterministic env vars in tests via pytest monkeypatch.
