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
  - [x] Remove GraphIR pattern ops/modules and verification.
  - [x] Remove pattern op usage in converters.

## Progress log
- 2026-01-14: Started task setup; status set to in_progress.
- 2026-01-14: Removed GraphIR pattern ops/modules and converter references.
- 2026-01-14: Removed tests that exercised deleted GraphIR pattern ops.

## Patch summary
- Removed GraphIR bundle/pattern_expr ops and helper module.
- Dropped bundle/pattern_expr verification from GraphIR modules.
- Simplified GraphIR converters to drop pattern rebundling and binding checks.
- Removed GraphIR pattern op tests and rebundling coverage from atomization tests.

## PR URL
- https://github.com/Jianxun/ASDL/pull/135

## Verification
- `./venv/bin/pytest tests/unit_tests/ir`

## Status request (Done / Blocked / In Progress)
- Ready for review.

## Blockers / Questions
- None yet.

## Next steps
- Await review.
