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

## Patch summary
- `src/asdl/schema.py`: new shared schema generation helpers.
- `scripts/generate_schema.py`: refactor to call shared helper.
- `src/asdl/cli/__init__.py`: add `schema` subcommand with diagnostics.
- `tests/unit_tests/cli/test_netlist.py`: extend help assertions for `schema`.
- `tests/unit_tests/cli/test_schema.py`: new CLI schema output test.

## Verification
- Skipped per user request (netlist CLI tests handled by another task).

## Status request
- Done.

## Blockers / Questions
- Should CLI netlist tests be updated to accept backend header/comment lines, or is this a local config issue?

## Next steps
- Decide on netlist CLI expected output mismatch before marking Done.
