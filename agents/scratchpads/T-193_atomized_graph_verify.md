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
- [ ] Define diagnostic codes for atomized graph verification in the spec doc.
- [ ] Implement `verify_atomized_graph` helpers (pure functions; no mutation).
- [ ] Add unit tests covering each verifier error case.
- [ ] Document/implement caller-level gating to run verifier only when upstream diagnostics contain no ERROR.

## Progress log
- 2026-01-23: Scratchpad created; DoD updated with gating + distinct codes.
- 2026-01-23: Read executor context files and refactor specs; set T-193 to in_progress, ran lint_tasks_state, and created feature branch.

## Open questions
- None yet.
