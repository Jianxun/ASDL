# T-113 GraphIR program/module/device ops

## Task summary (DoD + verify)
- Create GraphIR dialect package with program/module/device ops, stable ID attrs, and module port_order.
- Register the dialect and add minimal verify checks for program/module/device structure.
- Add focused tests for the new ops.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_graphir_program.py -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_graphir.md`
- `docs/specs/spec_asdl_graphir_schema.md`
- `src/asdl/ir/ifir/dialect.py`
- `src/asdl/ir/nfir/dialect.py`
- `tests/unit_tests/ir/test_ifir_dialect.py`

## Plan
- [x] Add GraphIR dialect package (`src/asdl/ir/graphir/`) with program/module/device ops and stable IDs.
- [x] Implement minimal verification for program/module/device structure and port_order handling.
- [x] Add unit tests for GraphIR program/module/device ops.

## Progress log
- Created feature branch and set task status to in_progress.
- Implemented GraphIR dialect ops/attributes and exports.
- Added unit tests for GraphIR program/module/device ops.
- Opened PR #119.

## Patch summary
- Added GraphIR dialect package and exported ASDL_GRAPHIR.
- Added unit tests for GraphIR program ops.
- Updated task tracking status/metadata.

## PR URL
- https://github.com/Jianxun/ASDL/pull/119

## Verification
- `venv/bin/pytest tests/unit_tests/ir/test_graphir_program.py -v`

## Status request
- Ready for review.

## Blockers / Questions
- None yet.

## Next steps
- Implement GraphIR dialect + tests, then run verify command.
