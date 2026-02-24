# T-307 — Implement `asdlc query bindings`

## Task summary (DoD + verify)
- DoD:
  Implement `asdlc query bindings` with required `--view-config` and
  `--view-profile` pairing and deterministic `(path, instance)` output
  ordering. Ensure payload rows include `authored_ref`, `resolved`, and
  `rule_id` according to the frozen v0 contract. Add regression tests for
  option validation, payload shape, and deterministic ordering.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_query_bindings.py -v`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs/spec_cli_query.md
- src/asdl/cli/query_runtime.py
- src/asdl/cli/__init__.py
- src/asdl/views/api.py
- src/asdl/views/resolver.py
- src/asdl/views/instance_index.py

## Plan
- [x] Inspect existing query runtime/CLI scaffolding and binding-related fixtures.
- [x] Add failing tests for query-bindings option validation, payload shape, and ordering.
- [x] Implement `query bindings` payload builder and CLI command wiring.
- [x] Run verification and capture results.

## Milestone notes
- Intake complete; context and DoD verified.
- Added failing tests for required option validation and deterministic binding payload shape.
- Implemented `query bindings` runtime payload builder and wired CLI command handling.
- Verified task-specific pytest target passes.

## Patch summary
- Added `tests/unit_tests/cli/test_query_bindings.py` covering:
  - required `--view-config` + `--view-profile` enforcement for `query bindings`
  - JSON envelope discriminator and payload shape
  - deterministic `(path, instance)` ordering with authored/resolved/rule fields
- Added `build_query_bindings_payload` in `src/asdl/cli/query_runtime.py`:
  - maps authored refs by hierarchical full path
  - emits sorted rows by `(path, instance)` with `authored_ref`, `resolved`, `rule_id`
- Added `query bindings` command in `src/asdl/cli/__init__.py`:
  - enforces command-specific required view-binding options
  - reuses shared runtime + JSON envelope helpers
  - emits `kind="query.bindings"`

## PR URL
- Pending PR creation.

## Verification
- `./venv/bin/pytest tests/unit_tests/cli/test_query_bindings.py -v` (pass)
- `PYTHONPATH=src ./venv/bin/pytest tests/unit_tests/cli/test_query_bindings.py tests/unit_tests/cli/test_query_cli_runtime.py tests/unit_tests/cli/test_query_tree.py -v` (pass)

## Status request (Done / Blocked / In Progress)
- Done

## Blockers / Questions
- None.

## Next steps
- Push branch, open PR, and set task status to `ready_for_review` with PR number.
