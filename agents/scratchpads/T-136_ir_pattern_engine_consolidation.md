# T-136 IR pattern engine consolidation

## Task summary (DoD + verify)
- Implement pattern expansion/atomization utilities in src/asdl/ir/patterns with
  full-expression endpoint expansion (expand then split on '.') and literal-part
  preservation. Provide API hooks to reject splice delimiters for $ nets. Ensure
  collision detection, size limits, and diagnostics align with spec wording
  (pattern expression terminology). Add unit tests covering expansion,
  atomization, endpoint splitting, and $ net splice rejection.
- Verify: venv/bin/pytest tests/unit_tests/ir -v

## Read
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs/spec_asdl_pattern_expansion.md

## Plan
- [x] Inspect existing pattern utilities and specs; map gaps to T-136 scope.
- [x] Add tests first for expansion/atomization/endpoint splitting and $ splice rejection.
- [x] Implement pattern expansion/tokenization/atomization utilities in
  src/asdl/ir/patterns with spec-aligned diagnostics.
- [x] Run targeted IR tests and update scratchpad with results.

## Progress log
- 2026-02-08: Task set to in_progress, branch created.
- 2026-02-08: Added IR pattern engine tests and implementations; updated exports.
- 2026-02-08: Ran IR unit tests.

## Patch summary
- Added IR pattern engine expansion/atomization/tokenization utilities with
  spec-aligned diagnostics and splice rejection hooks.
- Added IR unit tests for pattern expansion, atomization, endpoint splitting,
  and splice rejection.

## PR URL
- None yet.

## Verification
- ./venv/bin/pytest tests/unit_tests/ir -v

## Status request (Done / Blocked / In Progress)
- In Progress.

## Blockers / Questions
- None yet.

## Next steps
- Review existing pattern helper implementations and write TDD cases.
