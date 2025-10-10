# Compiler / Core Pipeline Todo List

## Next Sprint – Linter & Compiler Architecture Refactoring
- [ ] xDSL Phase 0 – IR Bring-up
  - [X] Add optional `xdsl` extra in `pyproject.toml` (pin after local validation)
  - [X] Scaffold dialect package under `src/asdl/ir/` (module init)
  - [X] Define and register `ModuleOp`, `InstanceOp`, `WireOp`
  - [X] Implement `PortAttr`, `RangeAttr`, `ExprAttr`
  - [ ] Add uniqueness verifiers (modules, instances, wires)
  - [ ] Add pin count and name matching verifiers
  - [ ] Implement AST→IR converter skeleton with locations
  - [X] Preserve declared port order in IR printing (no implicit sorting)
  - [X] Implement `asdlc ir-dump --verify --run-pass <list>` CLI
  - [ ] Add deterministic name canonicalizer helper
  - [ ] Add SPICE parity normalizer stub (diff stability)
  - [X] Tests: create fixture ASDLs under `tests/fixtures/ir/`
  - [ ] Tests: golden textual IR for small fixture(s)
  - [X] Tests: dialect printing/parsing round-trip on fixtures (smoke via CLI xdsl)
  - [X] Tests: assert strict port order preservation in IR dump
  - [ ] Deliverable: IR prints and verifies on fixtures (parity approximate; minor diffs allowed)

### Netlist IR (Phase 0 mini)
- [X] Dialect scaffold: `netlist.module`, `netlist.instance` with `pin_map` and `pin_order`
- [X] Lowering: AST→Netlist IR (modules + instances; no nets yet)
- [X] CLI: `asdlc ir-dump --engine xdsl --lower netlist` and `--lower netlist-text`
- [X] Emitter: neutral textual netlist with `--sim {ngspice, neutral}` (default ngspice)
- [ ] Propagate instance/module parameters into Netlist IR and emitter

## Backlog – Generator Improvements
- [ ] Enhanced error handling for malformed ASDL files
- [ ] Support for additional SPICE device types
- [ ] Optimizations for large hierarchical designs

## Backlog – IR Passes (Next Phase)
- [ ] PatternExpansionPass scaffold and tests (Phase 1)

## Testing & Refinements
- [ ] Thoroughly test `serialization.py` module

---
## Completed (see `context/done.md` for full archive)
- Parser refactoring & location tracking ✅
- Elaborator pattern expansion system ✅
- Validation extraction & new diagnostic pipeline ✅
- SPICEGenerator modernization & full test coverage ✅ 