# T-320 — Unify hierarchy path identity helpers for query and views

## Task summary (DoD + verify)
- DoD: Audit path composition/parsing logic used by query bindings and view resolver/index data models, then isolate shared path helper(s) to avoid duplicated full-path string assembly. Migrate `asdl.views.instance_index`, `asdl.views.resolver`, and `asdl.cli.query_runtime` to use the shared helper(s), preserving output payload contracts. Record legacy path logic removed and new shared helper API in the scratchpad.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_query_bindings.py tests/unit_tests/views/test_view_apply.py -v`

## Read (paths)
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_cli_query.md`
- `src/asdl/views/instance_index.py`
- `src/asdl/views/resolver.py`
- `src/asdl/cli/query_runtime.py`
- `tests/unit_tests/cli/test_query_bindings.py`
- `tests/unit_tests/views/test_view_apply.py`

## Plan
- [x] Perform reuse audit for full-path assembly and path identity logic.
- [x] Isolate shared path helper(s) and migrate query/views callers.
- [x] Remove duplicated string-assembly logic from callers.
- [x] Add/update regressions for payload/path contract stability.
- [x] Run verify command and document removed duplicates.

## Milestone notes
- Intake: `T-320` was `ready` with `T-317`/`T-318`/`T-319` already done; moved to `in_progress` and linted task state.
- Reuse audit:
  - Duplicate full-path assembly existed in `ViewInstanceIndexEntry.full_path`, `ResolvedViewBindingEntry.full_path`, and `build_query_bindings_payload`.
  - Duplicate path-scope containment logic existed in `_entry_matches_scope` (`full == path or startswith(path + ".")`).
- Shared helper API isolated in `src/asdl/views/pathing.py`:
  - `join_hierarchy_path(parent_path: str, instance: str) -> str`
  - `is_path_within_scope(full_path: str, scope_path: str) -> bool`
- Migration:
  - `asdl.views.instance_index` now uses shared helpers for `full_path` and scope matching.
  - `asdl.views.resolver` now uses shared helper for `full_path`.
  - `asdl.cli.query_runtime` now uses shared helper for query-bindings full-path lookup key assembly.

## Patch summary
- Added shared path identity module:
  - `src/asdl/views/pathing.py`
- Removed duplicated path assembly/scope checks from:
  - `src/asdl/views/instance_index.py`
  - `src/asdl/views/resolver.py`
  - `src/asdl/cli/query_runtime.py`
- Added regression coverage for shared helper behavior:
  - `tests/unit_tests/cli/test_query_bindings.py`

## PR URL
- Pending PR creation.

## Verification
- `./venv/bin/pytest tests/unit_tests/cli/test_query_bindings.py tests/unit_tests/views/test_view_apply.py -v` (pass, 6 tests)

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Push branch and open PR to `main`.
- Set `T-320` to `ready_for_review` with PR number and lint task state.
