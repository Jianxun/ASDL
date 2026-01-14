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
- Triage existing pattern-binding verification helpers and diagnostics usage in GraphIR->IFIR and atomization.
- Introduce `src/asdl/patterns/verify.py` with pure helpers for expansion length mismatch + literal collision detection.
- Rewire GraphIR->IFIR conversion and pattern atomization to use helpers, preserving diagnostics codes/messages.
- Update `src/asdl/patterns/__init__.py` exports if needed and adjust tests.

## Progress log
- 2026-01-XX: Initialized scratchpad.

## Patch summary
- None yet.

## PR URL
- None yet.

## Verification
- Not run yet.

## Status request
- In Progress.

## Blockers / Questions
- None yet.

## Next steps
- Inspect current helpers and diagnostics usage for pattern binding verification.
