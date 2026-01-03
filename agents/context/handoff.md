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
- MVP pipeline orchestrator implemented with xDSL pass pipeline and an end-to-end pipeline test.
- T-036 CLI netlist command merged under `src/asdl/cli/` with tests passing locally (PR #31).
- T-043 list-only endpoint authoring enforced in AST/converter with parser coverage merged (PR #32).
- T-037 PARSE-003 diagnostics updated with endpoint list and instance expr hints merged (PR #33).
- T-041 device ports optional support merged with AST/IR/netlist coverage (PR #34).
- T-035 IFIR/emit diagnostics now attach source spans where available (PR #35).
- T-038 netlist template placeholders updated to `{ports}` (optional); reserved placeholder enforcement removed; CLI help/tests updated (PR #36).

## Last verified status
- `venv/bin/pytest tests/unit_tests/ast`
- `venv/bin/pytest tests/unit_tests/ir`
- `venv/bin/pytest tests/unit_tests/parser`
- `venv/bin/pytest tests/unit_tests/netlist`
- `venv/bin/pytest tests/unit_tests/e2e`
- `venv/bin/pytest tests/unit_tests/cli`
- `venv/bin/pytest tests/unit_tests/ir tests/unit_tests/netlist`

## Next steps (1-3)
1. Review PR #36 for T-038 and merge when approved.
2. Start T-039 CLI help task.

## Risks / unknowns
- IFIR and emission semantics are new; tests will drive final API shape.
- Backend-specific emission rules beyond ngspice remain undefined.
