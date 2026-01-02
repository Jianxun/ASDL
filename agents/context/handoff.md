# Handoff

## Current state
- MVP specs live under `docs/specs_mvp/` for AST, NFIR, IFIR, and ngspice emission; full specs remain under `docs/specs/`.
- MVP pipeline is now AST -> NFIR -> IFIR -> ngspice emission (CIR removed for MVP; NLIR renamed to IFIR).
- Clean slate for IR implementation; prior CIR/NLIR tasks archived.
- New OKR tracking lives in `agents/context/okrs.md`.
- AST models + parser updated to MVP net-first schema; parser/AST tests refreshed.
- ASDL_NFIR dialect + AST->NFIR conversion implemented with unit tests.

## Last verified status
- `venv/bin/pytest tests/unit_tests/ir`
- `venv/bin/pytest tests/unit_tests/parser`

## Next steps (1-3)
1. Implement ASDL_IFIR dialect and NFIR->IFIR conversion per MVP spec (T-032).
2. Implement ngspice emitter from IFIR per MVP emission spec (T-033).
3. Add end-to-end MVP pipeline test (T-034).

## Risks / unknowns
- IFIR and emission semantics are new; tests will drive final API shape.
- Backend-specific emission rules beyond ngspice remain undefined.
