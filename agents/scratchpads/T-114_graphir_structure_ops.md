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

## Plan
- Inspect existing GraphIR dialect structure and tests.
- Add net/instance/endpoint ops + verification rules per spec.
- Write tests for valid/invalid module graphs.
- Run verify command and update scratchpad.

## Progress log
- 2026-01-XX: Initialized scratchpad and task context.

## Patch summary
- TBD

## PR URL
- TBD

## Verification
- TBD

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None

## Next steps
- Inspect GraphIR dialect and spec for op definitions.
