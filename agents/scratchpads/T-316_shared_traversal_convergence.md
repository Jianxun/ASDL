# T-316 — Shared traversal convergence and guardrail tests

## Task summary (DoD + verify)
- DoD: Add convergence coverage that jointly validates module-only behavior for views indexing and module+device behavior for query tree after shared traversal migration. Confirm duplicate traversal/module-selection logic is removed from migrated subsystems and shared utility is the sole source of hierarchy traversal truth.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/views/test_instance_index.py tests/unit_tests/cli/test_query_tree.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [x] Validate current shared traversal usage and identify any remaining duplicate traversal/module-selection logic in views/query runtime.
- [x] Add/adjust tests proving convergence and guardrails for module-only vs module+device behavior.
- [x] Run targeted verification and update this scratchpad with results before handoff.

## Milestone notes
- Intake complete.
- Added convergence/guardrail tests to assert:
  - views index remains module-only while query tree includes module+device nodes.
  - migrated consumers no longer carry local top-resolution helpers.
- Refactored shared top-resolution behavior into public
  `asdl.core.hierarchy.resolve_top_module`, and removed duplicate local helpers
  from views/query runtime.

## Patch summary
- Added guardrail/convergence tests:
  - `tests/unit_tests/views/test_instance_index.py`
  - `tests/unit_tests/cli/test_query_tree.py`
- Updated shared hierarchy API:
  - `src/asdl/core/hierarchy.py` now exports `resolve_top_module`.
- Removed duplicated top-resolution helpers from migrated consumers:
  - `src/asdl/views/instance_index.py`
  - `src/asdl/cli/query_runtime.py`

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_instance_index.py tests/unit_tests/cli/test_query_tree.py -v`
  - Result: 13 passed

## Status request (Done / Blocked / In Progress)
- In Progress (awaiting PR creation + state flip to `ready_for_review`).

## Blockers / Questions
- None currently.

## Next steps
- Push branch and open PR to `main`.
- Update `agents/context/tasks_state.yaml` to `ready_for_review` with PR number.
