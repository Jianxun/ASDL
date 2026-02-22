# T-298 - Support occurrence-specific view application for reused module definitions

## Task summary (DoD + verify)
- DoD: Remove the non-uniform rewrite failure mode in view-binding application so path-scoped overrides work when the same module definition is reused at different hierarchy paths with different resolved refs. Keep sidecar semantics unchanged and ensure emission uses per-occurrence resolved refs deterministically.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view_fixture_binding_profiles_change_emitted_instance_refs or non_uniform or scoped_override or divergent" -v`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/views/api.py`
- `src/asdl/views/instance_index.py`
- `src/asdl/views/resolver.py`
- `src/asdl/emit/netlist/render.py`
- `tests/unit_tests/views/test_view_apply.py`
- `tests/unit_tests/cli/test_netlist.py`

## Plan
1. Reproduce behavior with targeted view/CLI tests.
2. Replace module-key uniform rewrite logic in `apply_resolved_view_bindings` with occurrence-specific specialization logic.
3. Add regression coverage for divergent path overrides on reused module definitions.
4. Run verify command and record results.

## Milestone notes
- Intake complete: task was `ready`; set to `in_progress`; linted task state.
- Implemented occurrence-specialized rewrites in `apply_resolved_view_bindings` with deterministic clone naming for diverging reused module occurrences.
- Added regressions:
  - unit test for non-uniform shared module rewrite now handled by specialization.
  - CLI test asserting sidecar entries plus emitted refs for divergent scoped overrides on reused module definitions.

## Patch summary
- `src/asdl/views/api.py`
  - Removed non-uniform shared-module error path.
  - Added path-based recursive specialization of module instances.
  - Added deterministic collision-safe specialized module naming (`__occ_<sha1_8>`).
  - Kept sidecar/index strict matching checks unchanged.
- `tests/unit_tests/views/test_view_apply.py`
  - Added regression for divergent descendant rewrites across reused module definitions.
- `tests/unit_tests/cli/test_netlist.py`
  - Added self-contained divergent scoped-override fixture + config.
  - Added CLI regression checking sidecar ordering/content and emitted call refs (`leaf_alt`, `leaf_dbg`).

## PR URL
- Pending (branch prepared; PR to open during closeout).

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view_fixture_binding_profiles_change_emitted_instance_refs or non_uniform or scoped_override or divergent" -v`
  - Result: 4 passed, 26 deselected.

## Status request (Done / Blocked / In Progress)
- In Progress (implementation + verification complete; closeout pending PR creation and task-state finalization).

## Blockers / Questions
- None.

## Next steps
1. Commit implementation and regression changes.
2. Push feature branch and open PR to `main`.
3. Update `agents/context/tasks_state.yaml` to `ready_for_review` with PR number and lint task state.
