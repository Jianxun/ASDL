# T-214: Netlist renderer consumes NetlistIR

## Objective
Refactor netlist rendering to accept `NetlistDesign` dataclasses directly,
use NetlistIR index helper for lookups, and preserve emission parity.

## Key requirements (from task card)
- Accept NetlistIR dataclasses instead of xDSL IFIR ops.
- Use NetlistIR index helper for `(ref_file_id, ref)` resolution.
- Preserve deterministic ordering and template/params/variables behavior.
- Add tests covering NetlistIR render parity.

## Implementation notes
- Replace xDSL op traversal with iteration over `NetlistDesign.modules`.
- Use `NetlistIRIndex` from `emit/netlist/ir_utils.py` for symbol lookup.
- Ensure connection ordering mirrors existing `_ordered_conns` logic:
  - If ref is a module: use module `ports` list.
  - If ref is a device: use device `ports` list.
- Keep `templates.py` placeholder validation logic untouched.
- Merge params/variables using existing `params.py` helpers (strings in NetlistIR).

## Tests
- Add/adjust tests in `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`
  to render a NetlistIR design and compare output to expected fixture strings.

## Files
- `src/asdl/emit/netlist/render.py`
- `src/asdl/emit/netlist/ir_utils.py`
- `src/asdl/emit/netlist/templates.py`
- `src/asdl/emit/netlist/params.py`
- `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py`
