# Compiler / Core Pipeline Todo List

## Next Sprint – Linter & Compiler Architecture Refactoring
- [ ] Parser Hardening (TDD)
  - [ ] P102: Missing Required Section
  - [ ] P103: Invalid Section Type
  - [ ] P201: Unknown Field (Warning)
- [ ] SPICEGenerator Refactoring Pipeline
  - [ ] Refactor generator to use Elaborator outputs
  - [ ] Deprecate PatternExpander
- [ ] Tooling Back-Ends
  - [ ] Create `scripts/asdl_linter.py`

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