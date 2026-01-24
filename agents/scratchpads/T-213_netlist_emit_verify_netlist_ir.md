# T-213: Netlist verification consumes NetlistIR

## Objective
Refactor netlist emission verification to take `NetlistDesign` dataclasses as
the primary input, reuse `verify_netlist_ir(...)` for structural checks, and
preserve backend/template validation semantics without relying on xDSL ops.

## Key requirements (from task card)
- Accept NetlistIR dataclasses in `emit/netlist/verify.py`.
- Reuse `verify_netlist_ir(...)` for structural rules.
- Add NetlistIR index helper for `(file_id, name)` lookups in `ir_utils.py`.
- Preserve diagnostics parity for missing backend, placeholder validation, and
  variable merge errors.
- Tests for NetlistIR verification in emit path without xDSL dependencies.

## Implementation notes
- Introduce a `NetlistIRIndex` helper in `emit/netlist/ir_utils.py`:
  - `modules_by_key: dict[tuple[str | None, str], NetlistModule]`
  - `devices_by_key: dict[tuple[str | None, str], NetlistDevice]`
  - `top_name` resolution for `NetlistDesign`.
- Port `VerifyNetlistPass`-style logic into a pure function operating on
  NetlistIR (`verify_netlist_emit_netlist_ir(...)` or similar).
- Call `verify_netlist_ir(...)` first, then run backend-specific checks.
- Keep diagnostic codes/messages aligned with existing emit verifier.

## Tests
- Add a new unit test in `tests/unit_tests/emit/test_netlist_emit_verify.py`
  that builds a minimal `NetlistDesign` with a device backend and verifies
  diagnostics parity (e.g., missing backend or unknown placeholder).
- Ensure tests do not import xDSL.

## Files
- `src/asdl/emit/netlist/verify.py`
- `src/asdl/emit/netlist/ir_utils.py`
- `tests/unit_tests/emit/test_netlist_emit_verify.py`
