# T-323 Scratchpad

## Task summary (DoD + verify)
- DoD: Carry module parameters into NetlistIR and replace emitter-local ad-hoc
  module param access with `NetlistModule.parameters` as source of truth for
  `__subckt_header__` vs `__subckt_header_params__` dispatch.
- Verify:
  - `./venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py tests/unit_tests/emit/test_netlist_ir_model.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`

## Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/emit/netlist_ir.py`
- `src/asdl/lowering/atomized_graph_to_netlist_ir.py`
- `src/asdl/emit/netlist/render.py`
- `tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py`
- `tests/unit_tests/emit/test_netlist_ir_model.py`
- `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`

## Plan
1. Add regression expectations for module parameter propagation and header dispatch.
2. Add first-class `parameters` to `NetlistModule` and populate from atomized lowering.
3. Switch netlist header dispatch to use `NetlistModule.parameters`.
4. Run verify command and capture results.

## Milestone notes
- Reuse audit: reused lowering helper `_to_string_dict` and emitter helper
  `_dict_attr_to_strings` + existing `_format_params_tokens`; no backend-name
  conditionals added.
- TDD check: added failing tests first, then implemented model/lowering/render
  support until verify suite passed.

## Patch summary
- Added `parameters: Optional[Dict[str, str]]` to `NetlistModule`.
- Lowered `AtomizedModuleGraph.parameters` into `NetlistModule.parameters`.
- Updated netlist render header dispatch to read module parameters from
  `NetlistModule.parameters` directly.
- Added regressions proving:
  - module parameters are preserved in NetlistIR lowering;
  - NetlistIR model construction supports module parameters;
  - header template dispatch uses parameterized header only when module
    parameters are non-empty.

## PR URL
- TBD

## Verification
- PASS: `./venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py tests/unit_tests/emit/test_netlist_ir_model.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`

## Status request (Done / Blocked / In Progress)
- In Progress (ready to open PR)

## Blockers / Questions
- None.

## Next steps
1. Commit and push branch.
2. Open PR against `main`.
3. Update `agents/context/tasks_state.yaml` to `ready_for_review` with PR number.
