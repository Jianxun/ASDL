# Backlog – Validation & DRC

## Cross-Reference Validation
- [ ] Detect and warn about circular dependencies between modules
- [ ] Validate parameter references (undefined parameters used)
- [ ] Check for orphaned nets (declared but never connected)
- [ ] Validate port width consistency in pattern expansions

## Design-Rule Checking (DRC)
- [ ] Basic electrical rules (no floating inputs/outputs)
- [ ] Port direction consistency checking
- [ ] Parameter range validation
- [ ] Device constraint validation (W/L ratios, etc.)

## Parameter Resolution (Deferred)
- [ ] Implement robust parameter resolution in `Elaborator`
- [ ] Handle hierarchical scope & expressions
- [ ] Diagnostics for undefined & circular parameters 