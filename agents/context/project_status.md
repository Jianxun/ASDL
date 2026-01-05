# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- MVP specs live under `docs/specs_mvp/` for AST, NFIR, IFIR, and ngspice emission; full specs remain under `docs/specs/` pending reconciliation.
- MVP pipeline is AST -> NFIR -> IFIR -> emit; NLIR and CIR are merged into IFIR.
- Clean slate for IR implementation; prior CIR/NLIR tasks archived.
- OKR tracking is deprecated; planning is spec-driven.
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
- T-039 CLI help test added to verify command listing (PR #37).
- T-046 individual merged parameter values now exposed as template placeholders; templates can reference device/backend/instance params directly (e.g., `{L}`, `{W}`, `{NF}`, `{m}`).
- T-047 system devices refactor complete: ngspice emitter now uses backend config (`config/backends.yaml`) with 5 required system devices; all hardcoded ngspice syntax removed; all tests passing with byte-for-byte identical output.
- T-048 complete: unified netlist backend with CLI `--backend` (default `sim.ngspice`), backend config `extension`, and dedicated netlist verification pass; `emit_ngspice` removed.
- T-049 complete: split `src/asdl/emit/netlist.py` into `src/asdl/emit/netlist/` package with API/verify/render/templates/params/IR helpers/diagnostics; updated codebase map; tests passing; PR https://github.com/Jianxun/ASDL/pull/41.

## Last verified status
- `venv/bin/pytest tests/unit_tests/ast`
- `venv/bin/pytest tests/unit_tests/ir`
- `venv/bin/pytest tests/unit_tests/parser`
- `venv/bin/pytest tests/unit_tests/emit -v`
- `venv/bin/pytest tests/unit_tests/netlist`
- `venv/bin/pytest tests/unit_tests/e2e`
- `venv/bin/pytest tests/unit_tests/cli`
- `venv/bin/pytest tests/unit_tests/ir tests/unit_tests/netlist`
- `venv/bin/python -m py_compile src/asdl/emit/netlist/*.py`

## Next steps (1-3)
1. T-053: Preserve the raw pattern tokens through AST/NFIR/IFIR so downstream passes can trust lexemes before expansion.
2. T-057: Deliver the standalone pattern expansion engine (ranges/alternation/splicing) and prove it via parser tests and diagnostics.
3. T-058/T-059: Follow with pattern binding verification (length/endpoint constraints) and then a coordinated elaboration pass so IFIR/netlist outputs consume concrete names.

## Risks / unknowns
- Coordinating pattern expansion across AST, NFIR, IFIR, and netlist diagnostics is currently the highest ambiguity.
- IFIR and emission semantics are new; tests will drive final API shape.
- Backend-specific emission rules beyond ngspice remain undefined.
- System devices successfully decouple backend syntax; backend config schema is evolving to include output extensions.
