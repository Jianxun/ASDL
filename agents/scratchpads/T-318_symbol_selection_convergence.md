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
- [ ] Perform reuse audit for symbol-selection helpers in core/views.
- [ ] Implement shared symbol-selection helper and migrate callers.
- [ ] Remove duplicated local symbol-selection/existence logic.
- [ ] Add/update regressions for ambiguity and deterministic fallback.
- [ ] Run verify command and record source-of-truth APIs.

