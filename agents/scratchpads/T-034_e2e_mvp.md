# T-034 - MVP Pipeline Orchestration + E2E Test

## Goal
Implement the MVP pipeline orchestrator and add an end-to-end test covering
AST -> NFIR -> IFIR -> ngspice emission via the pipeline entrypoint.

## DoD
- Implement `src/asdl/ir/pipeline.py` entrypoint using xDSL PassManager.
- Wrap NFIR->IFIR conversion as a pass; gate verify passes via options.
- Return IFIR design + diagnostics; no user-facing exceptions.
- Test parses MVP YAML, runs the pipeline entrypoint, and emits ngspice netlist.
- Output is deterministic and respects top handling rules.
- Test uses `docs/specs_mvp/` as the source of truth for expected output.

## Files likely touched
- `src/asdl/ir/pipeline.py`
- `tests/unit_tests/e2e/`
- `tests/fixtures/` (if needed)
- `docs/specs_mvp/spec_pipeline_mvp.md`

## Verify
- `pytest tests/unit_tests/ir`
- `pytest tests/unit_tests/e2e`
