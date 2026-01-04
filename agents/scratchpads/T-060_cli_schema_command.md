# T-060 CLI Schema Command

## Task summary
- DoD: Add a CLI command `asdlc schema` that writes JSON + text schemas to an output directory (default: CWD), reusing the same generator logic as `scripts/generate_schema.py`. Update CLI help to list the new command and add CLI tests that assert the output files are created.
- Verify: `pytest tests/unit_tests/cli -v`

## Read
- `src/asdl/cli/__init__.py`
- `scripts/generate_schema.py`
- `src/asdl/ast/__init__.py`
- `tests/unit_tests/cli/`

## Plan
- Add a `schema` subcommand in the CLI entrypoint with an `--out` option.
- Reuse `build_json_schema()` and `render_text_schema()` (or import from `scripts/generate_schema.py` if refactored).
- Update CLI help and tests to cover the new command + outputs.

## Progress log
- Initialized scratchpad.

## Patch summary
- TBD.

## Verification
- TBD.

## Blockers / Questions
- None.

## Next steps
- Implement CLI command wiring and add tests.
