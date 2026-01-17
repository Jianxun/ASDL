# T-148 AST Schema Refactor

## Task summary
- DoD: Move schema generator helpers into `src/asdl/ast/schema.py`, update CLI
  and `scripts/generate_schema.py` imports to the new location, and refresh the
  text schema summary to annotate required vs optional top-level fields. Keep
  output filenames (`schema.json`, `schema.txt`) unchanged.
- Verify: `venv/bin/pytest tests/unit_tests/cli/test_schema.py -v`

## Notes
- Remove the root-level module (`src/asdl/schema.py`) as part of the clean move.
- Update `agents/context/codebase_map.md` to reflect the new location if needed.

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/schema.py`
- `src/asdl/cli/__init__.py`
- `scripts/generate_schema.py`
- `agents/context/codebase_map.md`

## Plan
- [x] Move schema helpers into `src/asdl/ast/schema.py` and update CLI/script imports.
- [x] Refresh the text schema summary to label required vs optional fields.
- [x] Update the codebase map for the new schema helper location.
- [x] Run schema CLI tests.

## Progress log
- Relocated schema generator helpers and updated imports; refreshed summary output labels.
- Added AST schema helper entry to the codebase map.
- Ran schema CLI test and opened PR.

## Patch summary
- Moved schema generation helpers into `src/asdl/ast/schema.py` and updated CLI/script imports.
- Text schema summary now labels top-level fields as required vs optional.
- Codebase map notes the new AST schema helper location.

## PR URL
- https://github.com/Jianxun/ASDL/pull/157

## Verification
- `venv/bin/pytest tests/unit_tests/cli/test_schema.py -v`

## Status request
- Done

## Blockers / Questions
- None

## Next steps
- None.
