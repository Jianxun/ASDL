# T-080 Netlist header timestamp placeholders

## Objective
Add emit-time placeholders for system netlist header/footer templates and document them in the MVP spec.

## DoD
- `emit_date` and `emit_time` placeholders are available for `__netlist_header__` and `__netlist_footer__`.
- A single timestamp is captured per netlist emission and threaded through render.
- Template validation accepts the new placeholders.
- MVP netlist emission spec documents the placeholders and template-driven behavior.
- Netlist tests cover deterministic substitution of the timestamp values.

## Files
- src/asdl/emit/netlist/api.py
- src/asdl/emit/netlist/render.py
- src/asdl/emit/netlist/templates.py
- tests/unit_tests/netlist/test_netlist_emitter.py
- docs/specs_mvp/spec_netlist_emission_mvp.md

## Verify
- pytest tests/unit_tests/netlist -v

## Notes
- Keep `{file_id}` semantics as entry file path for netlist header/footer.
- Prefer inject fixed timestamp in tests to avoid nondeterminism.
