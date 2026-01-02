# T-033 - ngspice Emission from IFIR (MVP)

## Task summary
- DoD: Implement ngspice emission from IFIR per `docs/specs_mvp/spec_netlist_emission_mvp.md` (top handling, named conns, device param merge/validation, backend template rendering); add golden tests.
- Verify: `pytest tests/unit_tests/netlist`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `agents/roles/executor.md`
- `docs/specs_mvp/spec_netlist_emission_mvp.md`
- `docs/specs_mvp/spec_asdl_ifir_mvp.md`
- `docs/code_styles/xdsl_style.md`
- `src/asdl/ir/nfir/dialect.py`
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/diagnostics/core.py`
- `src/asdl/diagnostics/__init__.py`
- `tests/unit_tests/ir/test_dialect.py`
- `tests/unit_tests/ir/test_converter.py`

## Plan
- Read `docs/specs_mvp/spec_netlist_emission_mvp.md` and current emit/IR code for IFIR.
- Implement ngspice emitter per spec (top handling, conns ordering, param validation, template rendering).
- Add golden tests for simple circuits and top handling.
- Run verify command.

## Progress log
- 2026-01-02: Initialized task, set status to In Progress, created/updated scratchpad structure.
- 2026-01-02: Implemented IFIR dialect and ngspice emitter; added netlist tests; ran netlist pytest.

## Patch summary
- `src/asdl/ir/ifir/dialect.py`: add IFIR dialect ops/attrs with verifiers.
- `src/asdl/ir/ifir/__init__.py`: export IFIR dialect symbols.
- `src/asdl/emit/ngspice.py`: implement ngspice emission from IFIR with diagnostics.
- `src/asdl/emit/__init__.py`: export emitter entry point.
- `tests/unit_tests/netlist/test_ngspice_emitter.py`: add golden tests for emission/top handling.

## Verification
- `venv/bin/pytest tests/unit_tests/netlist`

## Blockers / Questions
- None yet.

## Next steps
- Read emission spec and existing emit scaffolding to finalize implementation plan.
