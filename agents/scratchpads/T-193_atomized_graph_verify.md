# T-193 Add stateless verifiers for AtomizedGraph

## Task summary (DoD + verify)
- DoD: Implement pure verification helpers under `src/asdl/core/verify_atomized_graph.py` to validate AtomizedGraph integrity (unique net/instance names, endpoint references, endpoint ports against module/device ports lists). Diagnostics must use new `IR-0XX` codes (distinct from atomization `IR-00X` errors) and be documented in `docs/specs/spec_diagnostic_codes.md`. Verifier execution should be gated at the caller level so it runs only when atomization produced no ERROR diagnostics to avoid duplicate reporting.
- Verify: `venv/bin/pytest tests/unit_tests/core/test_atomized_graph_verify.py -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs_refactor/spec_refactor_atomized_graph.md`
- `docs/specs/spec_diagnostic_codes.md`

## Plan
- [x] Review existing AtomizedGraph verifier implementation + diagnostics docs.
- [x] Identify gaps vs DoD and adjust code/tests/docs if needed.
- [x] Run unit tests for atomized graph verification.
- [ ] Update scratchpad/task state and open PR.

## Progress log
- 2026-01-23 18:55 — Task intake; read context/specs + current AtomizedGraph verifier code; confirmed existing implementation appears aligned with DoD; next step update task state + branch.
- 2026-01-23 18:56 — Set T-193 to in_progress, ran lint_tasks_state, created feature branch; next step confirm no gaps and run tests.
- 2026-01-23 18:57 — Reviewed verifier/docs/tests for gaps; no code changes required; next step run unit tests.
- 2026-01-23 18:58 — Commit ec2a208 "Chore: start T-193 execution" (tasks_state + scratchpad); next step run unit tests.
- 2026-01-23 18:59 — Ran `venv/bin/pytest tests/unit_tests/core/test_atomized_graph_verify.py -v` (pass); next step update scratchpad/task state + open PR.
- 2026-01-23 19:00 — Commit cf976ee "Docs: log T-193 verification run" (scratchpad update); next step update task state + open PR.

## Open questions
- None yet.

## Patch summary
- In progress.

## Verification
- `venv/bin/pytest tests/unit_tests/core/test_atomized_graph_verify.py -v`

## PR URL
- Pending.

## Status request
- in_progress

## Blockers / Questions
- None.

## Next steps
- Confirm no gaps, run unit tests, update task state + open PR.
