# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- MVP specs live under `docs/specs_mvp/` for AST/NFIR/IFIR/emission; full specs remain under `docs/specs/`.
- Legacy pipeline is AST -> GraphIR (xDSL) -> IFIR -> emit; NFIR remains optional for AST projection.
- Refactor specs drafted under `docs/specs_refactor/` (PatternedGraph core, pattern service, migration plan); legacy pipeline remains default.
- Refactor Phase 1 tasks (T-180/T-181/T-182) are in the current sprint.
- Import resolver exists under `src/asdl/imports/` but is not yet wired into CLI/pipeline.
- Netlist emission is backend-config driven; placeholder disambiguation (`{file_id}`, `{sym_name}`, `{top_sym_name}`) is still pending.

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
1. Implement PatternedGraph core dataclasses + registries (T-180).
2. Implement refactor pattern service (parse/bind/expand with named-axis broadcast) (T-181).
3. Add PatternedGraph query/index helpers to support API/visualization (T-182).

## Risks / unknowns
- Coordinating pattern expansion semantics across legacy and refactor pipelines is currently the highest ambiguity.
- IFIR and emission semantics are new; tests will drive final API shape.
- Backend-specific emission rules beyond ngspice remain undefined.
- Import-aware compilation is partially implemented but not yet exercised end-to-end in CLI or pipeline tests.
