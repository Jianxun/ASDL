# T-319 — Deduplicate query and netlist view-resolution orchestration

## Task summary (DoD + verify)
- DoD: Audit shared query/netlist CLI flow for view option validation and resolve+apply view-binding orchestration, then extract reusable runtime helper(s) under `src/asdl/cli/` and migrate both `asdl.cli.query_runtime.build_query_runtime` and `asdl.cli.netlist` command flow to use them. Preserve diagnostics and exit-code behavior. Document what orchestration was reused vs isolated in the scratchpad.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_query_cli_runtime.py tests/unit_tests/cli/test_netlist.py -v`

## Read (paths)
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `docs/specs/spec_cli_query.md`
- `agents/adr/ADR-0037-cli-query-semantics.md`

## Plan
- [x] Perform reuse audit across query and netlist CLI orchestration.
- [x] Extract shared runtime/view-resolution helper(s) under `src/asdl/cli/`.
- [x] Migrate query and netlist command flows to shared helper(s).
- [x] Add/update tests proving diagnostics/exit-code parity.
- [x] Run verify command and summarize reused vs isolated functionality.

## Milestone notes
- 2026-02-26: Intake complete; set `T-319` to `in_progress`, ran `./venv/bin/python scripts/lint_tasks_state.py`, and created branch `feature/T-319-cli-runtime-orchestration-dedupe`.
- 2026-02-26: Reuse audit found two duplicated orchestration paths:
  - option pairing validation for `--view-config`/`--view-profile`
  - resolve + apply view bindings with the same failure gates (import failure, resolver diagnostics, apply error)
- 2026-02-26: Isolated shared runtime helpers in `src/asdl/cli/runtime_common.py` and migrated both query-runtime and netlist call sites.

## Patch summary
- Added shared helpers in `src/asdl/cli/runtime_common.py`:
  - `validate_view_binding_options(...)`
  - `resolve_and_apply_view_bindings(...)`
- Migrated `asdl.cli.query_runtime`:
  - `validate_query_common_options(...)` now delegates to shared option validation.
  - `build_query_runtime(...)` now delegates shared resolve+apply orchestration while preserving query-specific diagnostic code wiring.
- Migrated `asdl.cli.__init__.py` netlist flow:
  - replaced inline option validation with shared helper.
  - replaced inline resolve+apply block with shared helper.
- Added regression coverage:
  - `tests/unit_tests/cli/test_query_cli_runtime.py` now asserts shared option-validator behavior directly.
  - `tests/unit_tests/cli/test_netlist.py` now verifies netlist rejects unpaired `--view-config`/`--view-profile` flags with unchanged messages.

## PR URL
- Pending (branch not pushed yet).

## Verification
- `./venv/bin/pytest tests/unit_tests/cli/test_query_cli_runtime.py tests/unit_tests/cli/test_netlist.py -v` (pass, 34 passed)

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
- Push branch and open PR to `main`.
- Update `tasks_state.yaml` to `ready_for_review` with PR number and rerun linter.
