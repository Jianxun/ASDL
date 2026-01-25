# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- MVP specs live under `docs/specs_mvp/` for AST/NFIR/IFIR/emission; full specs remain under `docs/specs/`.
- Netlist emission runs end-to-end through the refactor pipeline (PatternedGraph -> AtomizedGraph -> NetlistIR -> netlist emitter); CLI uses NetlistIR.
- Legacy xDSL GraphIR/IFIR pipeline is slated for hard decommission; CLI `ir-dump` and xDSL IR code will be removed from the active tree.
- Refactor specs remain under `docs/specs_refactor/` (PatternedGraph core, pattern service, migration plan).
- Import resolver exists under `src/asdl/imports/` but is not yet wired into the core lowering path.
- Netlist emission is backend-config driven; placeholder disambiguation (`{file_id}`, `{sym_name}`, `{top_sym_name}`) is still pending.
- ADR-0022 forbids spliced net names; refactor specs updated and implementation queued (T-188).
- Planned refactor inspection tooling: PatternedGraph JSON dump + CLI `patterned-graph-dump` (T-189/T-190).
- Atomized core graph conversion and stateless verification passes are planned next (T-191/T-192/T-193).

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
1. Remove IFIR paths from netlist emission and verification (T-219).
2. Retire CLI `ir-dump` and legacy xDSL entrypoints (T-220).
3. Move legacy xDSL specs to `docs/legacy/` and quarantine IR code/deps (T-223/T-221/T-222).

## Risks / unknowns
- Coordinating pattern expansion semantics across legacy and refactor pipelines is currently the highest ambiguity.
- Hard decommissioning xDSL may affect any downstream users relying on `ir-dump` or GraphIR/IFIR APIs.
- Backend-specific emission rules beyond ngspice remain undefined.
- Import-aware compilation is partially implemented but not yet exercised end-to-end in CLI or pipeline tests.
