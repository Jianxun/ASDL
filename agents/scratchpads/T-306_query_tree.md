# T-306 — Implement `asdlc query tree`

## Task summary (DoD + verify)
- DoD:
  Implement `asdlc query tree` for all supported stages and output modes.
  Output entries must match the v0 JSON contract and deterministic ordering
  rules. Ensure emitted stage without explicit view profile uses baseline
  resolution semantics. Add regression coverage for shape, ordering, and
  stage-specific nullability.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_query_tree.py -v`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs/spec_cli_query.md
- src/asdl/cli/query_runtime.py
- src/asdl/cli/__init__.py
- src/asdl/views/instance_index.py
- src/asdl/emit/netlist/render.py

## Plan
- [x] Inspect existing query runtime and CLI plumbing from T-305.
- [x] Add failing tests for `asdlc query tree` shape/order/stage behavior.
- [x] Implement `query tree` command and runtime wiring.
- [x] Run verification and capture results.

## Milestone notes
- Intake complete; task state moved to `in_progress`.
- Added regression tests for authored/resolved/emitted stage semantics and deterministic order.
- Implemented shared tree payload generation in query runtime and wired CLI tree handler.
- Updated runtime baseline envelope test to match non-empty tree payload.

## Patch summary
- Added `build_query_tree_payload` in `src/asdl/cli/query_runtime.py`.
- Added stage-aware root + instance row construction with deterministic DFS-pre ordering from authored hierarchy.
- Added emitted-name mapping integration for emitted-stage rows via `build_emission_name_map`.
- Wired `query tree` command to emit real payload rows instead of scaffold `[]`.
- Added query-tree regression suite in `tests/unit_tests/cli/test_query_tree.py`.
- Updated `tests/unit_tests/cli/test_query_cli_runtime.py` envelope stability assertion for non-empty payload.

## PR URL
- Pending PR creation.

## Verification
- `PYTHONPATH=src ./venv/bin/pytest tests/unit_tests/cli/test_query_tree.py -v` (pass)
- `PYTHONPATH=src ./venv/bin/pytest tests/unit_tests/cli/test_query_tree.py tests/unit_tests/cli/test_query_cli_runtime.py -v` (pass)

## Status request (Done / Blocked / In Progress)
- Done

## Blockers / Questions
- None.

## Next steps
- Push branch, open PR, and mark T-306 `ready_for_review` with PR number.
