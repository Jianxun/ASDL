# T-138 Pattern import migration

## Objective
- Update imports to use asdl.ir.patterns and remove the legacy
  src/asdl/patterns module.

## Notes
- No compatibility shim; fix all call sites and tests.
- NFIR is being deprecated, but keep dialect compiling until removal.

## Files
- src/asdl/ir/nfir/dialect.py
- tests/unit_tests/parser/test_pattern_atomization.py
- tests/unit_tests/parser/test_pattern_expansion.py
- src/asdl/patterns/__init__.py
- src/asdl/patterns/atomize.py

## References
- agents/scratchpads/architect_scratchpad.md
- docs/specs/spec_asdl_pattern_expansion.md
