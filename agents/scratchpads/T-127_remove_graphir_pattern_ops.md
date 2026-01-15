# T-127 Remove GraphIR pattern ops

## Task summary (DoD + verify)
- Delete graphir bundle/pattern_expr ops and helpers, and clean the GraphIR
  dialect/module verification to drop bundle/pattern_expr support. Remove
  GraphIR exports for pattern ops and delete the graphir pattern helper
  module.
- Verify: none listed.

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Remove GraphIR pattern ops and related helpers/modules.
- Update GraphIR dialect/module verification to drop bundle/pattern_expr checks.
- Clean GraphIR exports and imports tied to pattern ops.
- Todo:
  - [ ] Remove GraphIR pattern ops/modules and verification.
  - [ ] Remove pattern op usage in converters.

## Progress log
- 2026-01-14: Started task setup; status set to in_progress.

## Patch summary
- None yet.

## PR URL
- None yet.

## Verification
- Not run (no verify commands listed).

## Status request (Done / Blocked / In Progress)
- In Progress.

## Blockers / Questions
- None yet.

## Next steps
- Remove pattern ops and helpers, update dialect/module verification, and clean exports.
