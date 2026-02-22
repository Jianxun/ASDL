# T-293 - Apply resolved view bindings to netlist emission input

## Task summary (DoD + verify)
- Ensure resolved view bindings are applied to emitted instance references before netlist rendering.
- Preserve deterministic sidecar ordering and existing emission naming/disambiguation behavior.
- Add regression proving two profiles can produce different emitted instance refs.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/cli/test_netlist.py -k "view and binding" -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`
- `src/asdl/views/api.py`
- `src/asdl/views/resolver.py`
- `src/asdl/views/instance_index.py`
- `src/asdl/cli/__init__.py`
- `tests/unit_tests/cli/test_netlist.py`

## Plan
1. Add failing tests for view-binding apply behavior and profile-dependent emitted refs.
2. Implement a pure apply transform that rewrites NetlistIR instance refs from resolved sidecar entries.
3. Wire CLI netlist command to emit from transformed design after successful resolution.
4. Run task verify and close out status.

## Milestone notes
- Intake: confirmed `T-293` is `ready`; moved to `in_progress`.
- TDD: added `tests/unit_tests/views/test_view_apply.py` and CLI regression for profile-driven output differences.
- Implementation: added `apply_resolved_view_bindings` API and called it in CLI before `emit_netlist`.

## Patch summary
- Added `apply_resolved_view_bindings` in `src/asdl/views/api.py`.
- Added apply-time validation for sidecar/index path parity and shared-module non-uniform rewrite conflicts.
- Added `VIEW_APPLY_ERROR` export in `src/asdl/views/__init__.py`.
- Updated CLI netlist flow in `src/asdl/cli/__init__.py` to apply resolved bindings before emission.
- Added new tests in:
  - `tests/unit_tests/views/test_view_apply.py`
  - `tests/unit_tests/cli/test_netlist.py`

## PR URL
- Pending

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/cli/test_netlist.py -k "view and binding" -v`
  - Result: passed (`3 passed, 15 deselected`)

## Status request
- In Progress (ready to open PR)

## Blockers / Questions
- None

## Next steps
- Push branch and open PR to `main`.
- Update `tasks_state` to `ready_for_review` with PR number and `merged: false`.
