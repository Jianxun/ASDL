# T-121: Centralize pattern binding verification helpers

## Task summary (DoD + verify)
- DoD: Add `src/asdl/patterns/verify.py` to host pure pattern-binding helpers, including explicit utilities for (1) expansion length mismatches and (2) literal collision detection after expansion/atomization. Wire these helpers into the GraphIR/IFIR path (GraphIR->IFIR conversion and pattern atomization), avoid IR type dependencies in the helpers, and preserve diagnostics codes + VerifyException message text. Behavior remains unchanged.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_graphir_patterns.py tests/unit_tests/ir/test_pattern_atomization.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [x] Review existing pattern-binding checks in GraphIR->IFIR and IFIR atomization.
- [x] Add `src/asdl/patterns/verify.py` with pure helpers for length mismatch + literal collisions.
- [x] Rewire IFIR atomization to use the centralized helpers.
- [x] Wire helper usage into GraphIR->IFIR conversion for bundle-based length checks.
- [x] Run verification tests.

## Progress log
- 2026-01-14: Initialized scratchpad and set task status to in_progress.
- 2026-01-14: Added pattern verify helpers, refactored atomization, and added GraphIR bundle length checks.

## Patch summary
- Added `src/asdl/patterns/verify.py` with length mismatch + literal collision helpers and exports.
- Refactored IFIR pattern atomization to use centralized helpers for mismatch/collision messages.
- Added GraphIR bundle-based length mismatch checks during GraphIR->IFIR conversion.

## PR URL
- None yet.

## Verification
- `venv/bin/pytest tests/unit_tests/ir/test_graphir_patterns.py tests/unit_tests/ir/test_pattern_atomization.py -v`

## Status request
- In Progress.

## Blockers / Questions
- None yet.

## Next steps
- Open PR and request review.
