# T-300 — Remove occurrence-specialized `__occ` view-apply naming and align with global emission naming

## Task summary (DoD + verify)
- DoD: Remove occurrence-specialized module naming (`__occ_<hash>`) from view binding application so emitted naming is governed only by the global collision allocator policy. Ensure mixed-view/path-scoped outcomes remain deterministic and represented via emission naming/disambiguation; if an unsupported non-uniform case remains, emit a clear diagnostic rather than silently specializing names. Update view apply/resolver/CLI regressions.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view or divergent or scoped or mixed" -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
1. Inspect current occurrence-specialization behavior in views API and connected tests.
2. Remove `__occ` specialization and route naming through global netlist collision allocator.
3. Update/extend view apply, resolver, and CLI tests for deterministic mixed/scoped outcomes.
4. Run task verify command and any targeted checks.
5. Prepare closeout notes and open PR.

## Milestone notes
- Intake complete: task selected (`T-300`), status set to `in_progress`, branch `feature/T-300-remove-occ-specialization` created.
- Implementation complete: removed `__occ` module-name specialization in view apply and switched to deterministic per-occurrence module `file_id` specialization so emission naming is handled by global allocator.
- Regression updates complete: view apply/resolver/CLI tests cover deterministic divergent path ordering and emitted disambiguation (`__2`, `__3`) without `__occ` symbols.

## Patch summary
- Updated `src/asdl/views/api.py`:
  - Removed occurrence module renaming helper.
  - Added deterministic occurrence module file-id specialization helper.
  - Rewrote apply recursion to specialize child module identity by `(name, file_id)` and keep names stable for global emission collision allocation.
- Updated `tests/unit_tests/views/test_view_apply.py`:
  - Adjusted assertions to resolve rewritten modules via `(ref, ref_file_id)`.
  - Added guard asserting no `__occ` module names are created.
- Updated `tests/unit_tests/views/test_view_resolver.py`:
  - Added deterministic DFS-order regression for divergent path-scoped rules.
- Updated `tests/unit_tests/cli/test_netlist.py`:
  - Extended divergent reuse regression to assert global allocator suffixes (`stage__2`, `stage__3`) and no `__occ` emitted refs.

## PR URL
- Pending (to be filled by PR metadata/task state).

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_view_apply.py tests/unit_tests/views/test_view_resolver.py tests/unit_tests/cli/test_netlist.py -k "view or divergent or scoped or mixed" -v` (passed: 17 selected tests)

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Open PR and move task to `ready_for_review` with PR number.
