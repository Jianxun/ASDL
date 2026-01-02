# Tasks

## Active OKR(s)
- See `agents/context/okrs.md`.

## Current Sprint
- T-027 | Status: Ready | Owner: Executor | DoD: Implement xDSL `asdl_nfir` dialect per MVP spec; update AST->NFIR converter to parse instance expr into ref+params, extract `port_order` from `$` nets, and carry devices/backends; add unit tests. | Verify: `pytest tests/unit_tests/ir` and `pytest tests/unit_tests/parser`. | Links: scratchpad `agents/scratchpads/T-027_nfir_mvp.md`.
- T-028 | Status: Ready | Owner: Executor | DoD: Implement xDSL `asdl_ifir` dialect per MVP spec and NFIR->IFIR conversion (invert nets to named conns, explicit nets, preserve `port_order`); add unit tests. | Verify: `pytest tests/unit_tests/ir`. | Links: scratchpad `agents/scratchpads/T-028_ifir_mvp.md`.
- T-029 | Status: Ready | Owner: Executor | DoD: Implement ngspice emitter from IFIR per MVP emission spec (top handling, named conns, device param merge/validation, backend template rendering); add golden tests. | Verify: `pytest tests/unit_tests/netlist`. | Links: scratchpad `agents/scratchpads/T-029_netlist_emission_mvp.md`.
- T-030 | Status: Ready | Owner: Executor | DoD: End-to-end MVP pipeline test: parse AST -> NFIR -> IFIR -> emit; validate determinism and top handling. | Verify: `pytest tests/unit_tests/e2e`. | Links: scratchpad `agents/scratchpads/T-030_e2e_mvp.md`.

## Backlog
- None.

## Done
- None.
