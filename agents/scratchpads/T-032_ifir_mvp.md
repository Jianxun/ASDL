# T-032 - ASDL_IFIR MVP Dialect + Conversion

## Task summary
DoD:
- Dialect ops/attrs implemented with verifiers where specified.
- NFIR->IFIR conversion inverts nets into named conns and emits explicit nets.
- `port_order` is preserved.
- Unit tests cover dialect printing/parsing and conversion outputs.

Verify:
- `pytest tests/unit_tests/ir`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `docs/specs_mvp/spec_ast_mvp.md`
- `docs/specs_mvp/spec_asdl_nfir_mvp.md`
- `docs/specs_mvp/spec_asdl_ifir_mvp.md`
- `docs/specs_mvp/spec_netlist_emission_mvp.md`

## Plan
1. Inspect existing NFIR dialect and conversion scaffolding in `src/asdl/ir/`.
2. Add `asdl_ifir` dialect ops/attrs/verifiers per MVP spec.
3. Implement NFIR->IFIR conversion (nets + conns inversion, preserve `port_order`).
4. Add/adjust unit tests for IFIR dialect and conversion.

## Progress log
- Read executor role, contract, tasks, handoff, and MVP specs.
- Created feature branch `feature/T-032-ifir-mvp`.
- Marked T-032 as In Progress in `agents/context/tasks.md`.
- Implemented ASDL_IFIR dialect ops/attrs/verifiers and NFIR->IFIR conversion.
- Added IFIR dialect/conversion unit tests.
- Ran `venv/bin/pytest tests/unit_tests/ir`.
- Opened PR https://github.com/Jianxun/ASDL/pull/28.

## Patch summary
- `agents/context/tasks.md`: mark T-032 as In Progress.
- `agents/context/tasks.md`: mark T-032 as Done and add PR link.
- `agents/scratchpads/T-032_ifir_mvp.md`: expand with required sections and initial notes.
- `src/asdl/ir/ifir/dialect.py`: add IFIR ops/attrs/verifiers and dialect registration.
- `src/asdl/ir/ifir/__init__.py`: export IFIR dialect surface.
- `src/asdl/ir/converters/nfir_to_ifir.py`: add NFIR->IFIR conversion.
- `src/asdl/ir/converters/__init__.py`: export NFIR->IFIR conversion.
- `src/asdl/ir/__init__.py`: export NFIR->IFIR conversion.
- `tests/unit_tests/ir/test_ifir_dialect.py`: add IFIR dialect tests.
- `tests/unit_tests/ir/test_ifir_converter.py`: add NFIR->IFIR conversion test.

## Verification
- `venv/bin/pytest tests/unit_tests/ir`

## Blockers / Questions
- None.

## Next steps
1. Review existing NFIR dialect/conversion code under `src/asdl/ir/`.
2. Implement IFIR dialect and conversion.
3. Add unit tests and run `pytest tests/unit_tests/ir`.
