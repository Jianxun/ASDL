# Task summary (DoD + verify)
- Add PatternOriginIndex + ParamPatternOriginIndex to core registries and exports.
- Expand PatternExpr protocol to include parsed fields used by the pattern service.
- Decide canonical annotation storage (registry vs bundle) and update tests.
- Verify: venv/bin/pytest tests/unit_tests/core/test_patterned_graph.py -v

# Read (paths)
- agents/context/contract.md
- docs/specs_refactor/spec_refactor_patterned_graph.md
- docs/specs_refactor/spec_refactor_pattern_service.md
- src/asdl/core/registries.py
- src/asdl/core/graph.py
- tests/unit_tests/core/test_patterned_graph.py

# Plan
- [ ] Update registry types and exports; keep optional-by-default semantics.
- [ ] Expand PatternExpr protocol to include parsed fields (segments/axes/axis_order/span).
- [ ] Align annotations policy and update tests accordingly.
- [ ] Run verification.

# Progress log
- 

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
