# T-079 End-to-end diagnostics span coverage

## Task summary (DoD + verify)
- DoD: Add e2e diagnostics tests that run parse/lower/emit flows with known failures and assert each emitted diagnostic has a populated `primary_span` (no `NO_SPAN_NOTE`). Cover at least one error from the parser, IR lowering, and netlist verification/emission stages.
- Verify: `pytest tests/unit_tests/e2e -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Inspect existing e2e/netlist diagnostics tests and helpers.
- Add coverage for parser, lowering, and netlist stages with span assertions.
- Run e2e tests and record results here.

## Todo
- [x] Review existing e2e pipeline tests and diagnostics helpers.
- [x] Add parser-stage failure test with span assertions.
- [x] Add IR lowering failure test with span assertions.
- [x] Add netlist verification/emission failure test with span assertions.
- [x] Run `pytest tests/unit_tests/e2e -v`.

## Progress log
- 2026-01-10: Set T-079 to in_progress, created feature branch, initialized scratchpad.
- 2026-01-10: Added e2e diagnostics span coverage tests for parser/IR/netlist stages.

## Patch summary
- Added e2e span-coverage helpers and tests for parser, IR lowering, and netlist diagnostics.

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/e2e -v`

## Status request
- In Progress.

## Blockers / Questions
- None.

## Next steps
- Review existing diagnostics helpers in e2e/netlist tests and implement span coverage.
