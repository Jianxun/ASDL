# Tasks

## Active OKR(s)
- See `agents/context/okrs.md`.

## Current Sprint
- T-034 | Status: Done | Owner: Executor | DoD: Implement MVP pipeline orchestrator in `src/asdl/ir/pipeline.py` using xDSL PassManager; wrap NFIR->IFIR conversion as a pass; gate verification passes via options; return IFIR design + diagnostics; align with `docs/specs_mvp/spec_pipeline_mvp.md`. Add end-to-end test that uses the pipeline entrypoint (no direct converter calls) to parse AST -> NFIR -> IFIR -> emit; validate determinism and top handling. | Verify: `pytest tests/unit_tests/ir` and `pytest tests/unit_tests/e2e`. | Links: scratchpad `agents/scratchpads/T-034_e2e_mvp.md`, PR https://github.com/Jianxun/ASDL/pull/30.

## Backlog
- T-035 | Status: Backlog | Owner: Architect | DoD: Decide how to map NFIR `src`/AST locations into IFIR conversion diagnostics; emit span-aware diagnostics (or document why spans are unavailable) for NFIR->IFIR conversion errors; update unit tests as needed. | Verify: `pytest tests/unit_tests/ir`. | Links: scratchpad `agents/scratchpads/T-035_ifir_diagnostics_spans.md`.
- T-036 | Status: Backlog | Owner: Executor | DoD: Implement CLI command that runs the MVP pipeline end-to-end via `src/asdl/ir/pipeline.py` and emits ngspice output (no direct converter calls); expose a `--verify` toggle and deterministic diagnostics; add CLI-level tests. Blocked on T-034 completion. | Verify: `pytest tests/unit_tests/cli`. | Links: scratchpad `agents/scratchpads/T-036_cli_pipeline.md`.

## Exploration candidates (informal)
- IFIR diagnostics spans: mapping strategy, edge cases, and test fixtures.
- CLI pipeline UX: command flow, error messaging, and file layout.
- Netlist emission validation: strictness vs warnings; validation stages.
- xDSL pipeline boundaries: pass split/merge opportunities and IR boundaries.
- Codebase map gaps: navigation audit for future Executors.

## Done
- T-033 | Status: Done | Owner: Executor | DoD: Implement ngspice emitter from IFIR per MVP emission spec (top handling, named conns, device param merge/validation, backend template rendering); add golden tests. | Verify: `pytest tests/unit_tests/netlist`. | Links: scratchpad `agents/scratchpads/T-033_netlist_emission_mvp.md`, PR https://github.com/Jianxun/ASDL/pull/29.
- T-032 | Status: Done | Owner: Executor | DoD: Implement xDSL `asdl_ifir` dialect per MVP spec and NFIR->IFIR conversion (invert nets to named conns, explicit nets, preserve `port_order`); add unit tests. | Verify: `pytest tests/unit_tests/ir`. | Links: scratchpad `agents/scratchpads/T-032_ifir_mvp.md`, PR https://github.com/Jianxun/ASDL/pull/28.
- T-031 | Status: Done | Owner: Executor | DoD: Implement xDSL `asdl_nfir` dialect per MVP spec; update AST->NFIR converter to parse instance expr into ref+params, extract `port_order` from `$` nets, and carry devices/backends; add unit tests. | Verify: `pytest tests/unit_tests/ir` and `pytest tests/unit_tests/parser`. | Links: scratchpad `agents/scratchpads/T-031_nfir_mvp.md`, PR https://github.com/Jianxun/ASDL/pull/27.
- T-030 | Status: Done | Owner: Executor | DoD: Rewrite AST + parser for MVP spec `docs/specs_mvp/spec_ast_mvp.md` (AsdlDocument with only `top/modules/devices`; `ModuleDecl` with `instances`/`nets` ordered maps of raw strings; `DeviceDecl` + `DeviceBackendDecl` with required template; enforce hard requirements and forbid legacy fields like ports/views/imports/exports; update `src/asdl/ast/__init__.py` exports + JSON schema); refresh parser/location tests for new schema and add AST validation tests. | Verify: `pytest tests/unit_tests/parser` and `pytest tests/unit_tests/ast`. | Links: scratchpad `agents/scratchpads/T-030_ast_parser_mvp.md`, PR https://github.com/Jianxun/ASDL/pull/26.
