# T-321 Scratchpad

## Task summary (DoD + verify)
- Implement parameter-presence dispatch for subckt system templates without
  backend-name conditionals:
  - `__subckt_header__` vs `__subckt_header_params__`
  - `__subckt_call__` vs `__subckt_call_params__`
- Keep `{params}` deterministic as space-delimited `key=value` tokens.
- Preserve placeholder validation reuse and whitespace collapsing behavior.
- Add regression coverage for ngspice/xyce/spectre backend-owned syntax.
- Verify command:
  - `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/emit/test_backend_config.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/emit/netlist/render.py`
- `src/asdl/emit/netlist/templates.py`
- `src/asdl/emit/backend_config.py`
- `examples/config/backends.yaml`
- `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`
- `tests/unit_tests/emit/test_backend_config.py`

## Plan
1. Add regression tests first (TDD) for parameterized system-template behavior
   and required backend config templates.
2. Implement dispatch and validation/config updates with shared helper reuse.
3. Run verify command and close out status/PR handoff.

## Milestone notes
- Added failing regression for backend-owned parameterized subckt call syntax
  (ngspice/xyce/spectre) to prove dispatch behavior.
- Implemented parameter-presence template selection and shared validation reuse.

## Patch summary
- Updated backend required system devices to include:
  - `__subckt_header_params__`
  - `__subckt_call_params__`
- Extended system template placeholder validation for new system devices.
- Reused `_validate_template` inside `_render_system_device` and expanded
  whitespace collapsing to include empty `{params}`.
- Added parameterized module-call dispatch:
  - if instance params present -> `__subckt_call_params__`
  - otherwise -> `__subckt_call__`
- Added module-header parameter dispatch support path:
  - if module params present -> `__subckt_header_params__`
  - otherwise -> `__subckt_header__`
- Added/updated examples backend templates for ngspice/xyce/spectre/klayout.
- Added tests:
  - backend config now expects/validates the two new required templates
  - render regression proves backend-owned syntax differences (`PARAMS:`,
    `parameters`, plain forms) without backend-name compiler branching

## PR URL
- Pending creation in closeout step.

## Verification
- `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/emit/test_backend_config.py -v`
  - Result: 20 passed

## Status request (Done / Blocked / In Progress)
- In Progress (ready to open PR and set `ready_for_review`).

## Blockers / Questions
- None.

## Next steps
1. Push branch and open PR to `main`.
2. Set `T-321` status to `ready_for_review` with PR number and lint task state.
