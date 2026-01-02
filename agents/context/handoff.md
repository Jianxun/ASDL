# Handoff

## Current state
- MVP specs live under `docs/specs_mvp/` for AST, NFIR, IFIR, and ngspice emission; full specs remain under `docs/specs/`.
- MVP pipeline is now AST -> NFIR -> IFIR -> ngspice emission (CIR removed for MVP; NLIR renamed to IFIR).
- Clean slate for IR implementation; prior CIR/NLIR tasks archived.
- New OKR tracking lives in `agents/context/okrs.md`.

## Last verified status
- Not verified after MVP spec updates.

## Next steps (1-3)
1. Implement ASDL_NFIR dialect and AST->NFIR conversion per MVP spec (T-027).
2. Implement ASDL_IFIR dialect and NFIR->IFIR conversion per MVP spec (T-028).
3. Implement ngspice emitter from IFIR per MVP emission spec (T-029).

## Risks / unknowns
- IFIR and emission semantics are new; tests will drive final API shape.
- Backend-specific emission rules beyond ngspice remain undefined.
