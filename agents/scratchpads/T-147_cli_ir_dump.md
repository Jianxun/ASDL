# Task summary (DoD + verify)
- DoD: Add `asdlc ir-dump` command to emit canonical GraphIR or IFIR to stdout or `-o/--output`. Support `--ir {graphir,ifir}` (default ifir), `--verify/--no-verify`, and `--lib` for import roots. For GraphIR, run import-resolution and optional verification before dumping. For IFIR, reuse the MVP pipeline. Emit diagnostics on stderr and exit non-zero on errors. Add CLI tests for graphir/ifir output.
- Verify: `venv/bin/pytest tests/unit_tests/cli/test_ir_dump.py -v`

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/cli/__init__.py
- src/asdl/ir/pipeline.py
- src/asdl/ir/dump.py
- tests/unit_tests/cli/test_netlist.py
- tests/unit_tests/ir/test_ir_dump.py

# Plan
- [x] Add pipeline helper for GraphIR verification path if needed for CLI.
- [x] Add CLI ir-dump command wired to GraphIR/IFIR dump utilities with diagnostics handling.
- [x] Add CLI tests for graphir/ifir dumps and output file behavior.
- [x] Run targeted CLI test.

# Progress log
- Implemented CLI ir-dump flow and GraphIR verification helper.
- Added CLI tests for IFIR stdout and GraphIR file output.
- Ran CLI ir-dump tests.

# Patch summary
- Added GraphIR verification helper and new ir-dump CLI command with diagnostics.
- Added CLI tests covering IFIR stdout and GraphIR file output.

# PR URL
- https://github.com/Jianxun/ASDL/pull/156

# Verification
- `venv/bin/pytest tests/unit_tests/cli/test_ir_dump.py -v`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- 

# Next steps
- Await review.
