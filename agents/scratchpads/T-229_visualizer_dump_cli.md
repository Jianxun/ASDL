# T-229: Visualizer Dump CLI

## Task summary (DoD + verify)
- Add `asdlc visualizer-dump` with `--module`, `--list-modules`, and `--compact` flags.
- Emit minimal JSON to stdout with `{schema_version, module, instances, nets, endpoints, registries, refs.modules, refs.devices}`.
- `--list-modules` outputs module list JSON for the entry file only.
- Diagnostics go to stderr; non-zero exit on failures. No files are written.
- Verify: `./venv/bin/asdlc visualizer-dump examples/**/*.asdl --list-modules`.

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Inspect CLI pipeline and existing dump helpers for patterns.
- Implement `visualizer-dump` command with minimal JSON output + diagnostics handling.
- Add/adjust tests if coverage exists for CLI output.
- Verify with the specified command.

## Progress log
- 2026-01-26 00:00 — Task intake: T-229 identified as ready; scratchpad initialized; next step update task state to in_progress.

## Patch summary

## PR URL

## Verification

## Status request
- In Progress

## Blockers / Questions

## Next steps
- Update task status to in_progress, lint task state, and inspect CLI pipeline for existing dump patterns.
- 2026-01-26 00:01 — Set T-229 status to in_progress and linted tasks_state; files touched: `agents/context/tasks_state.yaml`; next step inspect CLI pipeline and dump helpers.
- 2026-01-26 00:05 — Added CLI tests for visualizer-dump list/modules and module output; files touched: `tests/unit_tests/cli/test_visualizer_dump.py`; next step implement CLI + dump helpers.
- 2026-01-26 00:06 — Committed tests (f648983) "Add visualizer dump CLI tests"; next step implement visualizer dump serializer and CLI command.
- 2026-01-26 00:15 — Implemented visualizer dump JSON helpers and entry-module filtering; files touched: `src/asdl/core/dump.py`, `src/asdl/core/__init__.py`, `src/asdl/core/pipeline.py`, `src/asdl/cli/__init__.py`; next step commit and run tests.
- 2026-01-26 00:16 — Committed implementation (0fd559b) "Add visualizer dump serializer and CLI"; next step run CLI tests and verify command.
- 2026-01-26 00:17 — Ran `./venv/bin/pytest tests/unit_tests/cli/test_visualizer_dump.py`; result: 2 passed; next step run task verify command.
- 2026-01-26 00:20 — Updated visualizer-dump to accept multiple inputs with --list-modules; files touched: `src/asdl/cli/__init__.py`; next step re-run tests and verify.
- 2026-01-26 00:21 — Re-ran `./venv/bin/pytest tests/unit_tests/cli/test_visualizer_dump.py`; result: 2 passed; next step run verify command again.
