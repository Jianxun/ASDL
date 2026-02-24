# T-305 Query CLI foundation and shared runtime

## Task summary (DoD + verify)
- DoD: Add the `asdlc query` command group with shared/common options and
  validation, plus a reusable query runtime module that centralizes stage
  construction (`authored`/`resolved`/`emitted`), JSON envelope emission
  (`schema_version=1` and `kind`), and shared diagnostics/exit behavior.
  Enforce the spec rule that missing anchors are hard errors while valid
  empty results remain successful. Include focused CLI regression tests for
  common option validation and JSON envelope stability.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_query_cli_runtime.py -v`

## Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs/spec_cli_query.md

## Plan
- Inspect existing CLI plumbing and query-adjacent runtime helpers.
- Add regression tests for common query options and envelope behavior.
- Implement shared query runtime + command group wiring to satisfy tests.
- Run verify command and capture outcomes.

## Milestone notes
- Intake complete; implementation pending.
- Added query runtime foundation (`query_runtime.py`) with shared stage construction, common option validation helpers, deterministic JSON envelope helpers, and shared exit-code logic.
- Added `asdlc query` command group scaffold and `query tree` foundation wiring in CLI with shared option handling.
- Added focused CLI/runtime regressions for common option validation, JSON envelope stability, and authored/resolved/emitted stage construction.
- Ran task verify command; all tests pass.

## Patch summary
- `src/asdl/cli/query_runtime.py`
  - Added reusable query runtime module with:
    - `QueryStage` enum and `QueryRuntime` dataclass.
    - `query_common_options` decorator for shared query CLI options.
    - `validate_query_common_options` dependency checks.
    - `build_query_runtime` stage construction for authored/resolved/emitted.
    - JSON envelope and serialization helpers (`schema_version=1`, `kind`).
    - Shared diagnostics/exit semantics helper (`query_exit_code`) and output finalizer.
- `src/asdl/cli/__init__.py`
  - Added `asdlc query` group.
  - Added `asdlc query tree` scaffold command using shared options/runtime helpers.
  - Centralized validation for `--view-config/--view-profile` pairing via runtime helper.
- `tests/unit_tests/cli/test_query_cli_runtime.py`
  - Added regression tests for:
    - common option validation failures,
    - stable JSON envelope output for query tree,
    - stage construction behavior for authored/resolved/emitted,
    - shared envelope/exit helper behavior.

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/cli/test_query_cli_runtime.py -v`
  - Result: 5 passed.

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Implement T-305 scope and update verification.
