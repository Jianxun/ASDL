# T-051 Optional {name} Placeholder

## Context
Verification currently requires `{name}` in backend device templates. This blocks templates that are pure instructions and do not include device names.

## Notes
- Primary candidate files: `src/asdl/emit/netlist/templates.py`, `src/asdl/emit/netlist/verify.py`, `src/asdl/emit/netlist/render.py`, `tests/unit_tests/netlist/`.
- Keep `{ports}` optional; do not introduce new required placeholders.

## DoD
- `{name}` is no longer required by template validation.
- Diagnostics and tests updated to match the new rule.
- Netlist output unchanged for existing templates.
