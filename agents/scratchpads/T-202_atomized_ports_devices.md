# T-202 AtomizedGraph ports/devices propagation

## Task summary (DoD + verify)
- DoD: Update PatternedGraph -> AtomizedGraph lowering to consume module ports lists, propagate device definitions into the atomized program, and ensure atomized modules always carry ports lists. Update atomization tests.
- Verify: venv/bin/pytest tests/unit_tests/core/test_patterned_graph_atomize.py -v

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Inspect patterned graph atomization code paths and tests.
- Update lowering to carry module ports lists and device definitions into AtomizedGraph.
- Update atomization tests to assert ports/devices propagation.
- Run targeted tests.

## Todo
- [ ] Update atomization lowering to propagate ports list and devices.
- [ ] Update atomization tests for ports list/device propagation.
- [ ] Run targeted verification.

## Progress log
- 2026-01-23: Scratchpad created.
- 2026-01-23: Reviewed task scope and understood changes needed to propagate module ports and device definitions from PatternedGraph into AtomizedGraph lowering and update atomization tests accordingly.

## Patch summary
- TBD.

## PR URL
- TBD.

## Verification
- TBD.

## Status request (Done / Blocked / In Progress)
- In progress.

## Blockers / Questions
- None yet.

## Next steps
- Implement T-202 changes and update tests.
