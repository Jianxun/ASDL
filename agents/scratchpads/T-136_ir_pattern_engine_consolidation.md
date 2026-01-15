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
- [ ] Add tests first for expansion/atomization/endpoint splitting and $ splice rejection.
- [ ] Implement pattern expansion/tokenization/atomization utilities in
  src/asdl/ir/patterns with spec-aligned diagnostics.
- [ ] Run targeted IR tests and update scratchpad with results.

## Progress log
- 2026-02-08: Task set to in_progress, branch created.

## Patch summary
- None yet.

## PR URL
- None yet.

## Verification
- Not run yet.

## Status request (Done / Blocked / In Progress)
- In Progress.

## Blockers / Questions
- None yet.

## Next steps
- Review existing pattern helper implementations and write TDD cases.
