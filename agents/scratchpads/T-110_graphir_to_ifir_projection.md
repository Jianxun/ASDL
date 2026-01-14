# T-110 GraphIR to IFIR projection

## Task summary (DoD + verify)
- Implement GraphIR -> IFIR lowering as a thin projection and switch the netlist emitter to consume IFIR derived from GraphIR. Update IFIR and netlist tests to validate consistent output.
- Verify: `venv/bin/pytest tests/unit_tests/netlist/test_netlist_emitter.py -v`

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- docs/specs/spec_asdl_graphir.md
- docs/specs/spec_asdl_ifir.md
- src/asdl/ir/graphir/
- src/asdl/ir/ifir/
- src/asdl/emit/netlist/api.py
- tests/unit_tests/ir/test_ifir_converter.py
- tests/unit_tests/netlist/test_netlist_emitter.py

## Plan
- Add GraphIR -> IFIR converter and export helper in `asdl.ir`.
- Update netlist emission to accept GraphIR programs and project to IFIR.
- Adjust IFIR/netlist tests to exercise the GraphIR projection path.
- Run required netlist emitter verification.

## Progress log
- Added GraphIR projection tests and netlist GraphIR helper wiring.
- Implemented GraphIR -> IFIR projection and netlist conversion entry.
- Preserved entry file + src metadata through GraphIR conversion for netlist diagnostics.

## Patch summary
- Added GraphIR -> IFIR converter and export (`src/asdl/ir/converters/graphir_to_ifir.py`, `src/asdl/ir/__init__.py`).
- Netlist emission now accepts GraphIR programs and projects to IFIR (`src/asdl/emit/netlist/api.py`).
- Tests exercise GraphIR projection for IFIR converter and netlist emitter (`tests/unit_tests/ir/test_ifir_converter.py`, `tests/unit_tests/netlist/test_netlist_emitter.py`).

## PR URL
- https://github.com/Jianxun/ASDL/pull/125

## Verification
- `venv/bin/pytest tests/unit_tests/netlist/test_netlist_emitter.py -v`
  - Result: pass

## Status request
- Ready for Review

## Blockers / Questions
- 

## Next steps
- Await reviewer feedback.
