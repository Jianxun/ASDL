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
