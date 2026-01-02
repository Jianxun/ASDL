# T-029 - ngspice Emission from IFIR (MVP)

## Goal
Implement ngspice emission from IFIR per `docs/specs_mvp/spec_netlist_emission_mvp.md`.

## DoD
- Emitter renders named-only conns in deterministic order.
- Top handling supports default commented `.subckt`/`.ends` and `--top-as-subckt`.
- Device param merge + validation (warn and ignore unknown instance params).
- Backend templates render `{name}`, `{conns}`, `{params}` placeholders.
- Golden tests cover simple circuits and top handling.

## Files likely touched
- `src/asdl/emit/`
- `tests/unit_tests/netlist/`

## Verify
- `pytest tests/unit_tests/netlist`
