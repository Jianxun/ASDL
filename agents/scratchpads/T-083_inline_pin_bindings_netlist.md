# T-083 Inline pin bindings netlist coverage

## Objective
Add netlist/e2e coverage to ensure inline pin bindings produce correct connectivity and port order.

## DoD
- Netlist or e2e tests exercise inline pin bindings without listing every endpoint in `nets`.
- Include a case relying solely on inline bindings for internal nets.
- Include a case where `$` inline bindings create ports and impact emitted port order.

## Files
- tests/unit_tests/netlist/test_netlist_emitter.py
- tests/unit_tests/e2e/test_pipeline_mvp.py

## Verify
- pytest tests/unit_tests/netlist/test_netlist_emitter.py -v

## Notes
- Ensure tests are deterministic (no reliance on map order beyond specified port ordering rules).
