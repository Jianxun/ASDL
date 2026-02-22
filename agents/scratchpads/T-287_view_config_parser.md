# T-287 — Implement view config parser and validation models

## Task summary (DoD + verify)
- DoD: Add a new `asdl.views` config parser API for profile-based view binding (`view_order`, ordered `rules`, typed `match`) and validate schema rules from `spec_asdl_view_config.md`. Enforce `instance`/`module` mutual exclusion, assign deterministic default rule IDs (`rule<k>`), and emit deterministic diagnostics for malformed config payloads.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/views/test_view_config.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_view_config.md`
- `agents/adr/ADR-0033-view-binding-config-and-sidecar.md`

## Plan
- Add/extend view config models and parser API in `src/asdl/views/`.
- Implement schema validation and deterministic diagnostic behavior.
- Add unit tests for valid/invalid payloads and default rule IDs.
- Run focused verification.

## Milestone notes
- Intake complete.
- Added failing tests first for new view config parser API and validation behavior.
- Implemented `asdl.views` models and parser APIs with deterministic validation diagnostics.
- Verified focused views test suite passes.

## Patch summary
- Added a new `asdl.views` package:
  - `src/asdl/views/models.py`
  - `src/asdl/views/config.py`
  - `src/asdl/views/__init__.py`
- Implemented schema validation for:
  - required/non-empty `view_order`
  - typed `match` with at least one predicate
  - `instance` / `module` mutual exclusion
  - undecorated `module` predicate
  - bind symbol grammar (`cell` or `cell@view`)
- Added deterministic default rule IDs (`rule<k>`) per 1-based rule position.
- Added deterministic diagnostics for malformed payloads and YAML parse failures.
- Added unit tests in `tests/unit_tests/views/test_view_config.py` for happy-path and error-path coverage.

## PR URL
- Pending (to be populated from opened PR in execution report).

## Verification
- `./venv/bin/pytest tests/unit_tests/views/test_view_config.py -v` (pass; 5 passed)

## Status request (Done / Blocked / In Progress)
- Done

## Blockers / Questions
- None.

## Next steps
- Open PR and request review.
