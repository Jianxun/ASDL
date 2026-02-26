# T-320 — Unify hierarchy path identity helpers for query and views

## Task summary (DoD + verify)
- DoD: Audit path composition/parsing logic used by query bindings and view resolver/index data models, then isolate shared path helper(s) to avoid duplicated full-path string assembly. Migrate `asdl.views.instance_index`, `asdl.views.resolver`, and `asdl.cli.query_runtime` to use the shared helper(s), preserving output payload contracts. Record legacy path logic removed and new shared helper API in the scratchpad.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/cli/test_query_bindings.py tests/unit_tests/views/test_view_apply.py -v`

## Read (paths)
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `docs/specs/spec_cli_query.md`

## Plan
- [ ] Perform reuse audit for full-path assembly and path identity logic.
- [ ] Isolate shared path helper(s) and migrate query/views callers.
- [ ] Remove duplicated string-assembly logic from callers.
- [ ] Add/update regressions for payload/path contract stability.
- [ ] Run verify command and document removed duplicates.

