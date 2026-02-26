# T-323 Scratchpad

## Goal
Carry module `parameters` into NetlistIR and use it for subckt-header parameterized template dispatch.

## Reuse audit checklist
- Reuse existing AtomizedGraph->NetlistIR conversion helpers for string dicts.
- Reuse existing system-template rendering path; avoid backend-name branching.
- Reuse deterministic `k=v` token formatting behavior.

## Expected behavior
- `NetlistModule.parameters` is the header dispatch source of truth.
- `__subckt_header_params__` is selected when module parameters are non-empty.
- Existing `__subckt_call_params__` behavior remains intact.

## Verify
- `./venv/bin/pytest tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py tests/unit_tests/emit/test_netlist_ir_model.py tests/unit_tests/netlist/test_netlist_render_netlist_ir.py -v`
