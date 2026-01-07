# T-077 CLI import wiring and --lib roots

## Task summary
- **DoD**: Add a repeatable `--lib` option to `asdlc netlist` and pass the paths into the import-aware pipeline entrypoint. Use the pipeline's import diagnostics to gate output (errors abort, warnings allow netlist emission). Update CLI tests to cover `--lib`-driven resolution and `ASDL_LIB_PATH` fallback.
- **Verify**: `pytest tests/unit_tests/cli -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs_mvp/spec_cli_mvp.md`
- `src/asdl/cli/__init__.py`
- `src/asdl/ir/pipeline.py`
- `tests/unit_tests/cli/test_netlist.py`

## Plan
1. Add `--lib` option to CLI and plumb into pipeline call.
2. Gate CLI output on pipeline diagnostics (errors abort).
3. Extend CLI tests for `--lib` and env fallback.

## Todo
- [x] Add `--lib` CLI option (repeatable).
- [x] Wire CLI to import-aware pipeline entrypoint.
- [x] Update CLI tests for import resolution paths.

## Progress log
- Understanding: add repeatable `--lib` roots to `asdlc netlist`, route them into the import-aware pipeline, and rely on pipeline diagnostics for error gating while adding CLI coverage for `--lib` and `ASDL_LIB_PATH`.
- Added CLI tests for `--lib`-driven import resolution and `ASDL_LIB_PATH` fallback.
- Wired `asdlc netlist` to call the import-aware pipeline with entry file and lib roots.

## Patch summary
- Added CLI tests for import resolution via `--lib` and env fallback.
- Added `--lib` option to the netlist command and switched to entry-file pipeline invocation.

## Verification
- `./venv/bin/pytest tests/unit_tests/cli -v`

## Status request
- Ready for review (PR #78).

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
