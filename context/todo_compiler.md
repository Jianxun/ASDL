# Compiler / Core Pipeline Todo List

## Next Sprint – Linter & Compiler Architecture Refactoring
- [ ] xDSL Phase 0 – IR Bring-up
  - [ ] Add optional `xdsl` extra in `pyproject.toml` (pin after local validation)
  - [ ] Scaffold dialect package under `src/asdl/ir/` (module init)
  - [ ] Define and register `ModuleOp`, `InstanceOp`, `WireOp`
  - [ ] Implement `PortAttr`, `RangeAttr`, `ExprAttr`
  - [ ] Add uniqueness verifiers (modules, instances, wires)
  - [ ] Add pin count and name matching verifiers
  - [ ] Implement AST→IR converter skeleton with locations
  - [ ] Preserve declared port order in IR printing (no implicit sorting)
  - [ ] Implement `asdlc ir-dump --verify --run-pass <list>` CLI
  - [ ] Add deterministic name canonicalizer helper
  - [ ] Add SPICE parity normalizer stub (diff stability)
  - [ ] Tests: golden textual IR for `miller_ota`
  - [ ] Tests: dialect printing/parsing round-trip
  - [ ] Tests: assert strict port order preservation in IR dump
  - [ ] Deliverable: IR prints and verifies for `miller_ota`

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