# Task summary (DoD + verify)
- Implement AST->PatternedGraph lowering that builds ProgramGraph/ModuleGraph bundles with registries (pattern expressions, origins, source spans, schematic hints) without atomization.
- Return diagnostics instead of raising for malformed input.
- Add tests for a minimal module with patterned nets/endpoints and grouped endpoints.
- Verify: venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v

# Read (paths)
- agents/context/contract.md
- docs/specs_refactor/spec_refactor_patterned_graph.md
- docs/specs_refactor/spec_refactor_pattern_service.md
- src/asdl/core/graph.py
- src/asdl/core/registries.py

# Plan
- [ ] Define builder entrypoint and inputs/outputs.
- [ ] Implement lowering from AST structures to PatternedGraph bundles + registries.
- [ ] Add unit tests and run verification.

# Todo
- [ ] Draft tests for minimal patterned module + grouped endpoints.
- [ ] Implement build_patterned_graph lowering + registry wiring.
- [ ] Update core exports and docs/tests as needed.

# Progress log
- Understanding: Build a new AST -> PatternedGraph lowerer that produces ProgramGraph/ModuleGraph
  with parsed pattern expression registry, origin/source span metadata, and schematic group slices
  while avoiding atomization; invalid inputs should yield diagnostics instead of exceptions.

# Patch summary
- 

# Verification
- 

# Status request (Done / Blocked / In Progress)
- 

# Blockers / Questions
- 

# Next steps
- 
