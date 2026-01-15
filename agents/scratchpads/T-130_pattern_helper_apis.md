# T-130 Pattern metadata helper APIs

## Task summary (DoD + verify)
- Create new pattern metadata helpers under `src/asdl/ir/patterns` (origin, expr_table, parts, endpoint_split) and export them from the patterns package.
- Implement typed-attr encode/decode APIs described in ADR-0015; do not add binding logic here.
- Verify: none listed.

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/adr/ADR-0015-graphir-pattern-metadata.md

## Plan
- [x] Add unit tests for new pattern helper APIs.
- [x] Implement helper modules and exports.
- [x] Run targeted tests and record results.

## Progress log
- 2026-01-18: Set T-130 to in_progress, created feature branch, added tests + helper modules.
- 2026-01-18: Ran pattern helper unit tests.

## Patch summary
- Added pattern helper modules for origin, expression tables, pattern parts, and endpoint splitting with encode/decode helpers.
- Exported new helpers from `src/asdl/ir/patterns/__init__.py`.
- Added unit tests for helper APIs.

## PR URL
- https://github.com/Jianxun/ASDL/pull/138

## Verification
- `./venv/bin/python -m pytest tests/unit_tests/ir/test_pattern_helpers.py`

## Status request
- Ready for Review

## Blockers / Questions
- None yet.

## Next steps
- Open PR and update task status to ready_for_review.
