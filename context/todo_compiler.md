# Compiler / Core Pipeline Todo List

## Next Sprint – Linter & Compiler Architecture Refactoring
- [ ] xDSL Phase 0 – IR Bring-up
  - [ ] Add optional dependency extra for `xdsl`; set up CI matrix (macOS/Ubuntu; Py 3.10/3.11)
  - [ ] Define and register ASDL dialect ops/attrs (`ModuleOp`, `InstanceOp`, `WireOp`, `PortAttr`, `RangeAttr`, `ExprAttr`)
  - [ ] Implement AST→IR conversion skeleton (flattened `ASDLFile` input) with locations
  - [ ] Implement verifier skeletons (module/instance/wire uniqueness; pin count/name checks)
  - [ ] Implement `asdlc ir-dump --verify --run-pass <list>` CLI
  - [ ] Add golden textual IR for `examples/libs/ota_single_ended/miller_ota/miller_ota.asdl`
  - [ ] Add deterministic name canonicalizer and SPICE parity normalizer stub

## Backlog – Generator Improvements
- [ ] Enhanced error handling for malformed ASDL files
- [ ] Support for additional SPICE device types
- [ ] Optimizations for large hierarchical designs

## Testing & Refinements
- [ ] Thoroughly test `serialization.py` module

---
## Completed (see `context/done.md` for full archive)
- Parser refactoring & location tracking ✅
- Elaborator pattern expansion system ✅
- Validation extraction & new diagnostic pipeline ✅
- SPICEGenerator modernization & full test coverage ✅ 