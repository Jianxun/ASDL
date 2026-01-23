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
- [x] Define diagnostic codes for atomized graph verification in the spec doc.
- [x] Implement `verify_atomized_graph` helpers (pure functions; no mutation).
- [x] Add unit tests covering each verifier error case.
- [x] Document/implement caller-level gating to run verifier only when upstream diagnostics contain no ERROR.

## Progress log
- 2026-01-23: Scratchpad created; DoD updated with gating + distinct codes.
- 2026-01-23: Read executor context files and refactor specs; set T-193 to in_progress, ran lint_tasks_state, and created feature branch.
- 2026-01-23: Added AtomizedGraph verification helpers, gating wrapper, diagnostics spec entries, and unit tests.
- 2026-01-23: Opened PR #208 and prepared ready_for_review status update.
- 2026-01-23: Reviewer intake complete; PR targets main, set status to review_in_progress, linted tasks_state.
- 2026-01-23: Reviewed code/spec/test changes; no blockers found.
- 2026-01-23: Posted review comment, marked review_clean, proceeding to merge.

## Open questions
- None yet.

## Patch summary
- Added AtomizedGraph verification helpers with distinct IR codes and gated verification wrapper.
- Documented new AtomizedGraph verification diagnostics in spec.
- Added unit tests for duplicate names, endpoint references, port validation, and gating.

## Verification
- `venv/bin/pytest tests/unit_tests/core/test_atomized_graph_verify.py -v`

## PR URL
- https://github.com/Jianxun/ASDL/pull/208

## Status request
- ready_for_review

## Blockers / Questions
- None.

## Next steps
- Open PR, update tasks_state to ready_for_review, and record PR URL.
