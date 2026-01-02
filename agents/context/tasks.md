# Tasks

## Active OKR(s)
- See `agents/context/okrs.md`.

## Current Sprint
- T-030 | Status: Ready | Owner: Executor | DoD: Rewrite AST + parser for MVP spec `docs/specs_mvp/spec_ast_mvp.md` (AsdlDocument with only `top/modules/devices`; `ModuleDecl` with `instances`/`nets` ordered maps of raw strings; `DeviceDecl` + `DeviceBackendDecl` with required template; enforce hard requirements and forbid legacy fields like ports/views/imports/exports; update `src/asdl/ast/__init__.py` exports + JSON schema); refresh parser/location tests for new schema and add AST validation tests. | Verify: `pytest tests/unit_tests/parser` and `pytest tests/unit_tests/ast`. | Links: scratchpad `agents/scratchpads/T-030_ast_parser_mvp.md`.
- T-031 | Status: Ready | Owner: Executor | DoD: Implement xDSL `asdl_nfir` dialect per MVP spec; update AST->NFIR converter to parse instance expr into ref+params, extract `port_order` from `$` nets, and carry devices/backends; add unit tests. | Verify: `pytest tests/unit_tests/ir` and `pytest tests/unit_tests/parser`. | Links: scratchpad `agents/scratchpads/T-031_nfir_mvp.md`.
- T-032 | Status: Ready | Owner: Executor | DoD: Implement xDSL `asdl_ifir` dialect per MVP spec and NFIR->IFIR conversion (invert nets to named conns, explicit nets, preserve `port_order`); add unit tests. | Verify: `pytest tests/unit_tests/ir`. | Links: scratchpad `agents/scratchpads/T-032_ifir_mvp.md`.
- T-033 | Status: Ready | Owner: Executor | DoD: Implement ngspice emitter from IFIR per MVP emission spec (top handling, named conns, device param merge/validation, backend template rendering); add golden tests. | Verify: `pytest tests/unit_tests/netlist`. | Links: scratchpad `agents/scratchpads/T-033_netlist_emission_mvp.md`.
- T-034 | Status: Ready | Owner: Executor | DoD: End-to-end MVP pipeline test: parse AST -> NFIR -> IFIR -> emit; validate determinism and top handling. | Verify: `pytest tests/unit_tests/e2e`. | Links: scratchpad `agents/scratchpads/T-034_e2e_mvp.md`.

## Backlog
- None.

## Done
- None.
