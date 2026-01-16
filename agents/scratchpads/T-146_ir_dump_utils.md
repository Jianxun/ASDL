# T-146 Canonical GraphIR/IFIR dump utilities

## Task summary (DoD + verify)
- DoD: Add a small IR dump helper that returns deterministic textual output for GraphIR `graphir.program` and IFIR `asdl_ifir.design` using xDSL Printer defaults (no debuginfo). Output preserves region order and dictionary insertion order, and includes a trailing newline. Add unit tests that build a small GraphIR/IFIR via converters and assert the canonical dump matches expected text.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_ir_dump.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Update task state + branch.
- Inspect existing IR printer/dump and converter helpers.
- Implement canonical dump utility + exports.
- Add GraphIR/IFIR dump tests with expected output.
- Run verification.

## Todo
- [x] Add canonical dump helper + export
- [x] Add GraphIR/IFIR dump tests
- [x] Run verification

## Progress log
- 2026-01-XX: Initialized scratchpad.
- 2026-01-XX: Added dump helpers and canonical dump tests.

## Patch summary
- Added canonical GraphIR/IFIR dump helpers with trailing newline handling.
- Added IR dump tests asserting canonical printer output.

## PR URL
- Pending.

## Verification
- `venv/bin/pytest tests/unit_tests/ir/test_ir_dump.py -v`

## Status request
- In Progress.

## Blockers / Questions
- None.

## Next steps
- Inspect IR printing conventions and implement dump helper.
