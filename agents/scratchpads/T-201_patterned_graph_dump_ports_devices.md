# T-201 PatternedGraph dump ports/devices

## Task summary (DoD + verify)
- DoD: Update PatternedGraph JSON dump helpers to emit ports lists and device definitions. Adjust dump tests for the new JSON shape.
- Verify: venv/bin/pytest tests/unit_tests/core/test_patterned_graph_dump.py -v

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Inspect current PatternedGraph dump helpers and tests.
- Update JSON dump to include ports and device definitions.
- Update tests to assert new JSON shape.
- Run targeted tests.

## Progress log
- 2026-01-23: Scratchpad created.
- 2026-01-23: Updated PatternedGraph dump JSON to emit module ports and device definitions; adjusted dump tests to cover ports/devices.
- 2026-01-23: Ran venv/bin/pytest tests/unit_tests/core/test_patterned_graph_dump.py -v

## Patch summary
- Emitted module `ports` and device definitions in PatternedGraph JSON dumps.
- Added device fixtures and assertions for ports/devices in dump tests.

## PR URL
- TBD

## Verification
- venv/bin/pytest tests/unit_tests/core/test_patterned_graph_dump.py -v

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None yet.

## Next steps
- Open PR and update tasks_state to ready_for_review after push.
