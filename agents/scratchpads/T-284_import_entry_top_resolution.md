# T-284: Fix imported-program top inference to respect entry-file module scope

## Goal
When compiling an entry ASDL file with imports, allow omitted `top` if and only if
there is exactly one module in the entry file. Imported modules must not force
`top` to be mandatory.

## Scope
- Preserve `entry_file_id` for import-driven pipeline flows even when `top` is omitted.
- Resolve implicit top from entry-file modules only.
- Keep deterministic diagnostics when entry file has zero or multiple modules and no `top`.

## Suggested checks
- Entry file has one module + imports + no `top` -> emits using that entry module.
- Entry file has multiple modules + imports + no `top` -> `EMIT-001` missing top.
- Entry file has zero modules + imports + no `top` -> `EMIT-001` missing top.

## Candidate touch points
- `src/asdl/lowering/atomized_graph_to_netlist_ir.py`
- `src/asdl/lowering/__init__.py`
- `src/asdl/emit/netlist/ir_utils.py`
- `src/asdl/emit/netlist/render.py`
- `tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py`
- `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`
- `tests/unit_tests/cli/test_netlist.py`
