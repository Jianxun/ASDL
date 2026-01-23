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
- [x] Update atomization lowering to propagate ports list and devices.
- [x] Update atomization tests for ports list/device propagation.
- [x] Run targeted verification.

## Progress log
- 2026-01-23: Scratchpad created.
- 2026-01-23: Reviewed task scope and understood changes needed to propagate module ports and device definitions from PatternedGraph into AtomizedGraph lowering and update atomization tests accordingly.
- 2026-01-23: Updated atomization tests to cover module ports list expansion and device propagation.
- 2026-01-23: Updated atomization lowering to copy device definitions and expand module ports lists.
- 2026-01-23: Ran venv/bin/pytest tests/unit_tests/core/test_patterned_graph_atomize.py -v.
- 2026-01-23: Review started; status set to review_in_progress.

## Patch summary
- Propagated device definitions into AtomizedGraph and ensured module ports lists are expanded from PatternedGraph.
- Updated atomization tests to assert ports list expansion and device propagation.

## PR URL
- https://github.com/Jianxun/ASDL/pull/207

## Verification
- venv/bin/pytest tests/unit_tests/core/test_patterned_graph_atomize.py -v

## Status request (Done / Blocked / In Progress)
- Ready for review.

## Blockers / Questions
- None yet.

## Next steps
- Await reviewer feedback.
