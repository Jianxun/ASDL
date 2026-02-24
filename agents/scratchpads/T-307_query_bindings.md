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
- [ ] Add failing tests for query-bindings option validation, payload shape, and ordering.
- [ ] Implement `query bindings` payload builder and CLI command wiring.
- [ ] Run verification and capture results.

## Milestone notes
- Intake complete; context and DoD verified.

## Patch summary
- Pending.

## PR URL
- Pending PR creation.

## Verification
- Pending.

## Status request (Done / Blocked / In Progress)
- In Progress

## Blockers / Questions
- None.

## Next steps
- Implement via TDD, run verification, then open PR.
