# T-290 — Integrate view resolver into netlist CLI with sidecar output

## Task summary (DoD + verify)
- DoD: Add netlist CLI integration for view config/profile selection and optional binding sidecar output. Introduce `--view-config`, `--view-profile`, and `--binding-sidecar` options, run resolver before emission, and write deterministic sidecar JSON when requested. Resolution failures must emit diagnostics and terminate with non-zero exit.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_netlist.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`

## Plan
1. Inspect existing CLI netlist flow and view resolver/public API wiring.
2. Add CLI options and integrate config/profile resolution before emission.
3. Add deterministic sidecar JSON writing when requested.
4. Add/adjust CLI tests for success and failure paths.
5. Run verification and finalize task handoff.

## Milestone notes
- Intake complete; task set to `in_progress`.
- Added failing CLI tests for view config/profile + sidecar behavior and resolver failure exit path.
- Implemented view API + CLI integration for profile-based resolution and optional sidecar output.
- Verification command completed cleanly.

## Patch summary
- Added `asdl.views.api` with:
  - config+profile selection helper (`resolve_design_view_bindings`)
  - deterministic sidecar JSON projection helper (`view_sidecar_to_jsonable`)
  - diagnostics for missing profiles and resolver failures.
- Extended `asdlc netlist` with:
  - `--view-config`
  - `--view-profile`
  - `--binding-sidecar`
  - option-combination validation with diagnostics
  - resolver execution before emission and non-zero exit on failures
  - deterministic sidecar JSON write path.
- Added CLI regression tests covering:
  - successful sidecar emission with profile-based baseline view selection
  - failure path for unresolved baseline view candidates.

## PR URL
- Pending.

## Verification
- `./venv/bin/pytest tests/unit_tests/cli/test_netlist.py -v` (pass, 15 tests)

## Status request (Done / Blocked / In Progress)
- Done

## Blockers / Questions
- None.

## Next steps
- Push branch, open PR, set task `ready_for_review`.
