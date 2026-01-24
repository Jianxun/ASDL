# T-204 AtomizedGraph -> IFIR lowering scaffold and happy path

## Task summary (DoD + verify)
- Implement AtomizedGraph -> IFIR lowering under `src/asdl/lowering/atomized_graph_to_ifir.py` with a happy-path conversion that builds IFIR design, modules, nets, instances, and devices.
- Export the entry point in lowering `__init__` and add a unit test for the happy-path conversion.
- Verify with `venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v`.

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- [x] Define AtomizedGraph -> IFIR conversion API and diagnostics.
- [x] Implement happy-path lowering to IFIR ops and wire into lowering `__init__`.
- [x] Add happy-path unit test and run verify.

## Progress log
- 2026-01-23 20:23 — Task intake, read context, created scratchpad; next step set task status in progress and implement lowering.
- 2026-01-23 20:27 — Set T-204 to in_progress, created lowering scaffold and IFIR conversion, wired export; next step add tests and verify.
- 2026-01-23 20:27 — Commit 7d64472: add AtomizedGraph -> IFIR lowering scaffold; next step add happy-path test.
- 2026-01-23 20:28 — Added happy-path IFIR lowering test and ran pytest; next step commit test + update scratchpad.
- 2026-01-23 20:28 — Commit 38e61cc: add happy-path AtomizedGraph -> IFIR test; next step update scratchpad summary and close out.
- 2026-01-23 20:28 — Commit 5a11e19: update T-204 scratchpad progress; next step finalize closeout details.
- 2026-01-23 20:30 — Commit fad3766: update T-204 scratchpad summary; next step open PR and set ready_for_review.
- 2026-01-23 20:30 — Opened PR https://github.com/Jianxun/ASDL/pull/214; next step update task state and lint.
- 2026-01-23 20:32 — Review intake, confirmed scope and PR metadata; next step set review_in_progress and run required checks.
- 2026-01-23 20:33 — Set T-204 status to review_in_progress; next step run required tests.
- 2026-01-23 20:34 — Ran `venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v`; next step complete review and post findings.
- 2026-01-23 20:36 — Review decision: request_changes due to missing-endpoint errors not failing lowering; posted PR comment; next step await updates.
- 2026-01-23 20:30 — Set T-204 ready_for_review and linted tasks_state.yaml; next step finalize response.

## Patch summary
- Added AtomizedGraph -> IFIR lowering scaffold with basic reference handling.
- Exported new lowering entry point in `src/asdl/lowering/__init__.py`.
- Added happy-path unit test for AtomizedGraph -> IFIR conversion.

## PR URL
- https://github.com/Jianxun/ASDL/pull/214

## Verification
- `venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_ifir.py -v`

## Status request
- Ready for review.

## Blockers / Questions
- None yet.

## Next steps
- Implement conversion scaffolding and happy-path test.
