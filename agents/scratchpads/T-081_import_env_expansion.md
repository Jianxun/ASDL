# T-081 Import path env var expansion

## Task summary (DoD + verify)
- Import path resolution expands user home and env vars in `imports` values.
- `ASDL_LIB_PATH` entries expand user home and env vars.
- Malformed or empty expanded paths emit `AST-011` diagnostics.
- Tests cover env expansion for direct import paths and logical paths via `ASDL_LIB_PATH`.
- Import spec references the expansion behavior consistently.
- Verify: `pytest tests/unit_tests/parser/test_import_resolution.py -v`

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/imports/resolver.py
- tests/unit_tests/parser/test_import_resolution.py
- docs/specs/spec_asdl_import.md

## Plan
- [x] Add/extend tests for import/env expansion and malformed/empty cases.
- [x] Update import resolver expansion/diagnostics for imports + `ASDL_LIB_PATH`.
- [x] Align import spec wording with expansion/error behavior.

## Progress log
- 2026-01-08: Set T-081 status to in_progress and created feature branch.
- 2026-01-08: Added env expansion/failure tests and resolver validation updates.
- 2026-01-08: Updated import spec language and ran parser import tests.
- 2026-01-08: Opened PR for review.

## Patch summary
- Added env/tilde expansion validation and `ASDL_LIB_PATH` diagnostics for malformed roots.
- Added parser tests for env expansion, empty/missing vars, and env-root lookup.
- Documented expansion/error handling in the import spec.

## PR URL
- https://github.com/Jianxun/ASDL/pull/85

## Verification
- `./venv/bin/pytest tests/unit_tests/parser/test_import_resolution.py -v`

## Status request
- Ready for review.

## Blockers / Questions
- None.

## Next steps
- Await reviewer feedback.
