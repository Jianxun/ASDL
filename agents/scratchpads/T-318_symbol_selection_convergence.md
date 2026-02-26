# T-318 — Converge symbol-selection policy across hierarchy and views

## Task summary (DoD + verify)
- DoD: Audit existing symbol-selection/existence logic in hierarchy and views, then introduce one shared symbol-selection helper in `src/asdl/core/` that preserves deterministic `(file_id, symbol)` exact match and name-only fallback behavior. Migrate `asdl.core.hierarchy`, `asdl.views.resolver`, and `asdl.views.api` to consume the shared helper instead of local logic. Document in scratchpad which legacy helpers were removed and which shared APIs are now the source of truth. Add regressions covering ambiguous same-name symbols and deterministic fallback behavior.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/core/test_hierarchy.py tests/unit_tests/views/test_view_resolver.py tests/unit_tests/views/test_view_apply.py -v`

## Read (paths)
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `docs/specs/spec_hierarchy_traversal.md`
- `agents/adr/ADR-0038-shared-hierarchy-traversal.md`

## Plan
- [x] Perform reuse audit for symbol-selection helpers in core/views.
- [x] Implement shared symbol-selection helper and migrate callers.
- [x] Remove duplicated local symbol-selection/existence logic.
- [x] Add/update regressions for ambiguity and deterministic fallback.
- [x] Run verify command and record source-of-truth APIs.

## Milestone notes
- Intake: `T-318` started from `ready` after `T-317` was merged (`tasks_state`: done, PR 337).
- Reuse audit:
  - Legacy helper removed: `asdl.core.hierarchy._select_symbol`.
  - Legacy helpers removed: `asdl.views.resolver._build_symbol_indexes`, local name-count existence checks.
  - Migrated helper: `asdl.views.api._select_module` now delegates selection to shared core policy while preserving base-module fallback for missing provenance.
  - New source-of-truth API: `asdl.core.symbol_resolution.index_symbols`, `select_symbol`, `symbol_exists`.
- Regression added first (red): ambiguous-name fallback in view resolver with missing `ref_file_id`.
- Migration done: hierarchy traversal, view resolver baseline/final checks, and views apply path now consume shared core selection semantics.

## Patch summary
- Added shared helper module `src/asdl/core/symbol_resolution.py` with deterministic:
  - exact `(file_id, symbol)` selection precedence
  - name-only fallback (unique -> single; ambiguous -> declaration-order last)
  - existence checks via the same selection policy.
- Migrated `src/asdl/core/hierarchy.py` to remove local symbol-selection logic and use shared helper indexes/selections.
- Migrated `src/asdl/views/resolver.py` to reuse shared symbol indexes and existence checks for both baseline and final resolved symbol validation.
- Migrated `src/asdl/views/api.py` module selection path to shared helper while preserving base-module fallback isolation used for non-uniform specialization cases.
- Added regression in `tests/unit_tests/views/test_view_resolver.py`:
  - `test_resolve_view_bindings_uses_deterministic_fallback_for_ambiguous_symbols`.

## PR URL
- TBD

## Verification
- `./venv/bin/pytest tests/unit_tests/core/test_hierarchy.py tests/unit_tests/views/test_view_resolver.py tests/unit_tests/views/test_view_apply.py -v`
  - Result: PASS (19 passed)

## Status request
- In Progress (ready to open PR)

## Blockers / Questions
- None.

## Next steps
- Push feature branch, open PR to `main`, then set `T-318` to `ready_for_review` with PR number.
