# T-060 CLI Schema Command

## Task summary
- DoD: Add a CLI command `asdlc schema` that writes JSON + text schemas to an output directory (default: CWD), reusing the same generator logic as `scripts/generate_schema.py`. Update CLI help to list the new command and add CLI tests that assert the output files are created.
- Verify: `pytest tests/unit_tests/cli -v`

## Read
- `src/asdl/cli/__init__.py`
- `scripts/generate_schema.py`
- `src/asdl/ast/__init__.py`
- `src/asdl/__init__.py`
- `tests/unit_tests/cli/test_netlist.py`

## Plan
- Add shared schema generator helpers and reuse them in CLI + script.
- Add CLI `schema` subcommand with `--out` defaulting to CWD.
- Update CLI tests for help + output file creation.

## Progress log
- Initialized scratchpad.
- Added `asdl.schema` helpers and refactored schema generator script to reuse them.
- Added `schema` CLI command + tests; updated CLI help assertions.
- Ran CLI tests; netlist output assertions failed (extra header/comment lines).
- User requested skipping netlist CLI tests for this task.
- Opened PR: https://github.com/Jianxun/ASDL/pull/43
- Merged `origin/main` (T-050) and re-ran CLI tests.

## Patch summary
- `src/asdl/schema.py`: new shared schema generation helpers.
- `scripts/generate_schema.py`: refactor to call shared helper.
- `src/asdl/cli/__init__.py`: add `schema` subcommand with diagnostics.
- `tests/unit_tests/cli/test_netlist.py`: extend help assertions for `schema`.
- `tests/unit_tests/cli/test_schema.py`: new CLI schema output test.

## PR URL
- https://github.com/Jianxun/ASDL/pull/43

## Verification
- `venv/bin/pytest tests/unit_tests/cli -v`

## Status request
- Done.

## Blockers / Questions
- None.

## Next steps
- Merge PR 43.
