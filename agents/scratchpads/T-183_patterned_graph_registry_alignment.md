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
- Expanded PatternExpr protocol with parsed fields and added pattern origin registries.
- Removed bundle-level annotations in favor of registry-only storage.
- Updated PatternedGraph spec and tests; ran targeted pytest.

# Patch summary
- agents/context/tasks.yaml: add spec file to T-183 file list.
- agents/context/tasks_state.yaml: mark T-183 in progress.
- src/asdl/core/registries.py: add Axis/Pattern protocols + origin registries.
- src/asdl/core/graph.py: remove bundle annotations fields.
- src/asdl/core/__init__.py: export new registry/protocol types.
- docs/specs_refactor/spec_refactor_patterned_graph.md: align bundle/registry docs.
- tests/unit_tests/core/test_patterned_graph.py: extend registry optionality coverage.

# Verification
- venv/bin/pytest tests/unit_tests/core/test_patterned_graph.py -v

# Status request (Done / Blocked / In Progress)
- 

# Blockers / Questions
- 

# Next steps
- 
