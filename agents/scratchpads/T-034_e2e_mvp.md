# T-034 - MVP Pipeline Orchestration + E2E Test

## Task summary
- DoD: Implement MVP pipeline orchestrator in `src/asdl/ir/pipeline.py` using xDSL PassManager; wrap NFIR->IFIR conversion as a pass; gate verification passes via options; return IFIR design + diagnostics; align with `docs/specs_mvp/spec_pipeline_mvp.md`. Add end-to-end test that uses the pipeline entrypoint (no direct converter calls) to parse AST -> NFIR -> IFIR -> emit; validate determinism and top handling.
- Verify: `pytest tests/unit_tests/ir` and `pytest tests/unit_tests/e2e`.

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `docs/specs_mvp/spec_pipeline_mvp.md`
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/ir/converters/nfir_to_ifir.py`
- `src/asdl/ir/nfir/dialect.py`
- `src/asdl/ir/ifir/dialect.py`
- `src/asdl/emit/ngspice.py`
- `tests/unit_tests/netlist/test_ngspice_emitter.py`

## Plan
1. Inspect existing IR pipeline/converter/pass code to align with MVP spec and diagnostics flow.
2. Implement `src/asdl/ir/pipeline.py` entrypoint with PassManager ordering and verify gating.
3. Add end-to-end test using the pipeline entrypoint and ngspice emission; verify determinism/top handling.
4. Run required tests and update scratchpad/handoff/tasks.

## Progress log
- 2026-01-02: Created feature branch and set T-034 to In Progress.
- 2026-01-02: Implemented MVP pipeline orchestrator with xDSL pass pipeline.
- 2026-01-02: Added end-to-end pipeline test and verified pytest targets.

## Patch summary
- `src/asdl/ir/pipeline.py`: add MVP pipeline entrypoint with verify/convert passes and diagnostics handling.
- `src/asdl/ir/__init__.py`: export `run_mvp_pipeline`.
- `tests/unit_tests/e2e/test_pipeline_mvp.py`: add deterministic end-to-end pipeline test.
- `agents/context/tasks.md`: mark T-034 Done.
- `agents/context/handoff.md`: record pipeline completion and verification.

## Verification
- `venv/bin/pytest tests/unit_tests/ir` (pass)
- `venv/bin/pytest tests/unit_tests/e2e` (pass)

## Blockers / Questions
- None yet.

## Next steps
1. Inspect existing pipeline/pass code and tests.
2. Implement pipeline orchestrator per spec.
3. Add e2e pipeline test and run verifies.
