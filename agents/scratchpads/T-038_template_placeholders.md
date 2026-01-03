# T-038 Template Placeholders

## Task summary
- DoD: Update netlist template placeholders to use `{ports}` (hard switch; remove `{conns}`); treat `{ports}` as optional; only implicit placeholders are `{name}` and `{ports}` (others are user-controlled). Deprecate `{params}` placeholder and remove reserved-status enforcement; update validation rules/diagnostics and tests (missing `{ports}` allowed; unknown placeholders error). Update CLI help text to list supported placeholders.
- Verify: `pytest tests/unit_tests/netlist` and `pytest tests/unit_tests/cli`.

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.md
- agents/context/handoff.md
- agents/scratchpads/T-038_template_placeholders.md
- docs/specs_mvp/spec_netlist_emission_mvp.md
- src/asdl/emit/ngspice.py
- src/asdl/cli/__init__.py
- tests/unit_tests/netlist/test_ngspice_emitter.py
- tests/unit_tests/cli/test_netlist.py
- tests/unit_tests/ast/test_models.py
- tests/unit_tests/ir/test_converter.py
- tests/unit_tests/e2e/test_pipeline_mvp.py

## Plan
1. Update ngspice emitter placeholder validation and template values for `{ports}`, optional `{ports}`, and deprecated `{params}` with unknown placeholder errors intact.
2. Refresh tests and fixtures to use `{ports}` instead of `{conns}` and align expectations with new validation rules.
3. Update CLI help text to list supported placeholders.

## Progress log
- 2026-01-02: Created feature branch and set T-038 to In Progress.
- 2026-01-02: Loaded contract, tasks, handoff, specs, emitter, CLI, and tests.
- 2026-01-02: Updated ngspice emitter placeholder handling and whitespace cleanup.
- 2026-01-02: Refreshed tests/fixtures to use `{ports}` and adjusted diagnostics expectations.
- 2026-01-02: Updated CLI help text for supported placeholders.
- 2026-01-02: Opened PR https://github.com/Jianxun/ASDL/pull/36.

## Patch summary
- src/asdl/emit/ngspice.py: swap `{conns}` -> `{ports}`, make `{ports}` optional, remove reserved prop enforcement, and refine template cleanup.
- src/asdl/cli/__init__.py: document supported placeholders in help text.
- tests/unit_tests/netlist/test_ngspice_emitter.py: update placeholder usage and adjust placeholder/prop override expectations.
- tests/unit_tests/cli/test_netlist.py: update template fixture to `{ports}`.
- tests/unit_tests/e2e/test_pipeline_mvp.py: update template fixture to `{ports}`.
- tests/unit_tests/ast/test_models.py: update template example to `{ports}`.
- tests/unit_tests/ir/test_converter.py: update template example to `{ports}`.

## Verification
- `venv/bin/pytest tests/unit_tests/netlist` (pass)
- `venv/bin/pytest tests/unit_tests/cli` (pass)

## Blockers / Questions
- None.

## Next steps
- Await Architect review of PR #36.
