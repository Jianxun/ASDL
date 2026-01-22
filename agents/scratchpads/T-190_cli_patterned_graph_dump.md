# Task summary (DoD + verify)
- Add a `patterned-graph-dump` CLI command that parses AST, builds PatternedGraph via a core pipeline helper, and emits JSON to stdout or an output file (pretty by default, compact via flag). JSON-only output (no format switching) and no `--lib` option yet. Ensure diagnostics are emitted and exit codes match existing CLI conventions. Add CLI tests.
- Verify: `venv/bin/pytest tests/unit_tests/cli/test_patterned_graph_dump.py -v`

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Review CLI/pipeline patterns and PatternedGraph lowering entry points.
- Add a core pipeline helper for PatternedGraph imports/AST lowering.
- Implement CLI patterned-graph-dump output (pretty/compact, stdout/file).
- Add CLI tests and run the task verification command.

# Progress log
- Added a PatternedGraph pipeline helper and exported it from `asdl.core`.
- Implemented the `patterned-graph-dump` CLI command with compact output.
- Added CLI tests for stdout, compact file output, and missing input.

# Patch summary
- Added `src/asdl/core/pipeline.py` and exported the helper in `src/asdl/core/__init__.py`.
- Added `patterned-graph-dump` command in `src/asdl/cli/__init__.py`.
- Added CLI tests in `tests/unit_tests/cli/test_patterned_graph_dump.py`.

# PR URL
- https://github.com/Jianxun/ASDL/pull/200

# Verification
- `venv/bin/pytest tests/unit_tests/cli/test_patterned_graph_dump.py -v`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None.

# Next steps
- Await reviewer feedback.
