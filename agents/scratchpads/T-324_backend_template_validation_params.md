# T-324 Scratchpad

## Task summary (DoD + verify)
- DoD: Re-audit system-device template validation and backend sample templates
  so parameterized subckt templates align with ADR-0040/0041, tighten required
  template presence tests, and add regression assertions against
  `examples/config/backends.yaml` for ngspice/xyce/spectre parameterized
  header/call forms.
- Verify:
  `./venv/bin/pytest tests/unit_tests/emit/test_backend_config.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/emit/backend_config.py`
- `src/asdl/emit/netlist/templates.py`
- `tests/unit_tests/emit/test_backend_config.py`
- `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`
- `examples/config/backends.yaml`

## Plan
1. Reuse existing required-system-device validation path in
   `validate_system_devices`.
2. Tighten tests to explicitly exercise missing
   `__subckt_header_params__`/`__subckt_call_params__`.
3. Add golden assertions that load `examples/config/backends.yaml` and verify
   simulator-specific parameterized template syntax stays config-owned.
4. Verify with the task pytest command.

## Milestone notes
- Intake: T-324 is ready and dependencies T-323 and below are done.
- Reuse audit: no new validation algorithm needed; reused existing loader,
  required-device validation, and render test harness.
- Implementation: added targeted backend-config and netlist regression tests for
  parameterized template presence and golden syntax forms.

## Patch summary
- Updated backend config unit tests with:
  - targeted required-template absence test for parameterized subckt system
    devices,
  - golden config assertions for ngspice/xyce/spectre parameterized header/call
    template forms loaded from `examples/config/backends.yaml`.
- Updated netlist render regressions with:
  - a golden config emission test that loads `examples/config/backends.yaml` and
    asserts emitted parameterized subckt header/call lines for
    ngspice/xyce/spectre.

## PR URL
- Pending (to be created in closeout).

## Verification
- Ran:
  `./venv/bin/pytest tests/unit_tests/emit/test_backend_config.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`
- Result: 27 passed, 0 failed.

## Status request
- In Progress

## Blockers / Questions
- None.

## Next steps
1. Commit implementation and test updates.
2. Set task status to `ready_for_review` with PR number after opening PR.
