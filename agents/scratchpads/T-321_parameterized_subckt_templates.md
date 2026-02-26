# T-321 Scratchpad

## Goal
Implement parameterized subckt system-template dispatch without backend-name
conditionals in compiler code.

## Reuse audit checklist
- Reuse `_render_system_device` for all system template rendering.
- Reuse existing template placeholder validation in
  `src/asdl/emit/netlist/templates.py`.
- Reuse deterministic parameter string formatting conventions already used for
  device `{params}` rendering.

## Expected behavior
- Module header rendering:
  - no params -> `__subckt_header__`
  - params -> `__subckt_header_params__`
- Module call rendering:
  - no params -> `__subckt_call__`
  - params -> `__subckt_call_params__`
- `{params}` is emitted as deterministic space-delimited `key=value` tokens.
- Backend syntax remains template-owned (for example `PARAMS: {params}`).

## Verify
- `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/emit/test_backend_config.py -v`
