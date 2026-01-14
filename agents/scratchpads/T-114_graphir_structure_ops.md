# T-114 GraphIR net/instance/endpoint ops

## Task summary (DoD + verify)
- DoD: Add GraphIR net/instance/endpoint ops with stable IDs and implement
  module verification for net/instance name uniqueness and endpoint ownership
  plus endpoint uniqueness per (inst_id, port_path). Add tests covering valid
  and invalid module graphs.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_graphir_structure.py -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_graphir.md`
- `docs/specs/spec_asdl_graphir_schema.md`
- `src/asdl/ir/graphir/dialect.py`
- `tests/unit_tests/ir/test_graphir_program.py`

## Plan
- [x] Inspect existing GraphIR dialect structure and tests.
- [x] Add tests for valid/invalid module graphs.
- [x] Add net/instance/endpoint ops + module verification rules per spec.
- [x] Run verify command and update scratchpad.

## Progress log
- 2026-01-XX: Initialized scratchpad and task context.
- 2026-01-XX: Added GraphIR structure tests for module verification.
- 2026-01-XX: Implemented net/instance/endpoint ops and module verification.

## Patch summary
- Added GraphIR structure tests covering module uniqueness and endpoint rules.
- Added net/instance/endpoint ops plus symbol refs and module-level verification.

## PR URL
- https://github.com/Jianxun/ASDL/pull/120

## Verification
- `venv/bin/pytest tests/unit_tests/ir/test_graphir_structure.py -v`

## Status request (Done / Blocked / In Progress)
- Done

## Blockers / Questions
- None

## Next steps
- Await review feedback.
