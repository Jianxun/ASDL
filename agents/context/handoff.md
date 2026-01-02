# Handoff

## Current state
- MVP specs live under `docs/specs_mvp/` for AST, NFIR, IFIR, and ngspice emission; full specs remain under `docs/specs/`.
- MVP pipeline is now AST -> NFIR -> IFIR -> ngspice emission (CIR removed for MVP; NLIR renamed to IFIR).
- Clean slate for IR implementation; prior CIR/NLIR tasks archived.
- New OKR tracking lives in `agents/context/okrs.md`.
- AST models + parser updated to MVP net-first schema; parser/AST tests refreshed.
- ASDL_NFIR dialect + AST->NFIR conversion implemented with unit tests.
- ASDL_IFIR dialect + NFIR->IFIR conversion implemented with unit tests.
- ngspice emitter from IFIR implemented with MVP netlist tests.

## Last verified status
- `venv/bin/pytest tests/unit_tests/ir`
- `venv/bin/pytest tests/unit_tests/parser`
- `venv/bin/pytest tests/unit_tests/netlist`

## Next steps (1-3)
1. Add end-to-end MVP pipeline test (AST -> NFIR -> IFIR -> emit) (T-034).

## Risks / unknowns
- IFIR and emission semantics are new; tests will drive final API shape.
- Backend-specific emission rules beyond ngspice remain undefined.
