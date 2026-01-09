# T-080 Netlist header timestamp placeholders

## Task summary (DoD + verify)
- DoD: Add `emit_date` and `emit_time` placeholders for `__netlist_header__` and `__netlist_footer__` system devices. Capture a single emit timestamp per netlist (plumbed via `EmitOptions`/`emit_netlist`) and format it into the new placeholders. Template validation must accept the new placeholders. Update the MVP netlist emission spec to document the placeholders and that emission depends entirely on backend templates. Netlist tests must cover substitution with a deterministic timestamp.
- Verify: `pytest tests/unit_tests/netlist -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

## Plan
- Review current netlist emit options/render/template placeholder validation.
- Add emit timestamp capture and placeholder injection.
- Update tests and MVP spec to cover new placeholders.

## Todo
- [x] Review netlist emit flow, template validation, and tests.
- [x] Add emit timestamp plumbing to render/api.
- [x] Extend template placeholder validation for header/footer.
- [x] Add deterministic timestamp test coverage.
- [x] Update MVP netlist emission spec.
- [x] Run `pytest tests/unit_tests/netlist -v`.

## Progress log
- 2026-01-10: Set T-080 to in_progress, created feature branch, initialized scratchpad.
- 2026-01-10: Added emit timestamp placeholders and tests; updated netlist spec.

## Patch summary
- Added emit timestamp plumbing and placeholder validation for netlist header/footer.
- Added netlist tests for emit timestamp placeholders and stable backend config setup.
- Updated MVP netlist emission spec with emit timestamp placeholders and template-driven note.

## PR URL
- https://github.com/Jianxun/ASDL/pull/84

## Verification
- `./venv/bin/pytest tests/unit_tests/netlist -v`

## Status request
- Done.

## Blockers / Questions
- None.

## Next steps
- Inspect emit_netlist flow and template validation to identify where to inject timestamps.
