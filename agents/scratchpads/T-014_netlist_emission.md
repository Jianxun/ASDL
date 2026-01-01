# T-014 — Netlist Emission from IR

## Goal
Rebuild netlist/SPICE emission to consume xDSL IR (or add a short-lived IR→legacy adapter).

## References
- `docs/specs/spec_asdl_cir.md`

## Notes
- Preserve port ordering and named-only connectivity.
- Add small golden netlist tests to lock format.

## File hints
- `src/asdl/generator/`
- `src/asdl/ir/`
- `tests/unit_tests/netlist/`
