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
- [ ] Add/extend tests for import/env expansion and malformed/empty cases.
- [ ] Update import resolver expansion/diagnostics for imports + `ASDL_LIB_PATH`.
- [ ] Align import spec wording with expansion/error behavior.

## Progress log
- 2026-01-08: Set T-081 status to in_progress and created feature branch.

## Patch summary
- Pending.

## PR URL
- Pending.

## Verification
- Pending.

## Status request
- In Progress.

## Blockers / Questions
- None.

## Next steps
- Implement plan items and update verification.
