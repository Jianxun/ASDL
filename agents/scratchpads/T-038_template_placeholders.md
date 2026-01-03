# T-038 Template Placeholders

## Goal
Rework placeholder policy for netlist backend templates.

## Direction (2026-01-02 discussion)
- Hard switch `{conns}` -> `{ports}`; no alias support.
- `{ports}` is optional (templates may omit it).
- Only implicit placeholders are `{name}` and `{ports}`; other placeholders are user-controlled.
- `{params}` placeholder is deprecated; remove reserved-status enforcement.

## Files
- src/asdl/emit/ngspice.py
- src/asdl/cli/__init__.py (help text)
- tests/unit_tests/netlist/test_ngspice_emitter.py
- tests/unit_tests/cli/test_netlist.py or new help tests
