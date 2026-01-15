# T-136 IR pattern engine consolidation

## Objective
- Consolidate pattern expansion/atomization into src/asdl/ir/patterns with
  updated semantics (full-expression endpoint expansion, literal part
  preservation, and $ net splice rejection).

## Notes
- Do not treat src/asdl/patterns as golden; align with architect decisions.
- Endpoint expansion: expand the full expression, then split on '.' per atom.
- Preserve literal pattern parts exactly (no normalization).
- Provide API hooks to disallow splice delimiters when required (for $ nets).
- Diagnostics should use "pattern expression" terminology.

## Files
- src/asdl/ir/patterns/__init__.py
- src/asdl/ir/patterns/atomize.py
- src/asdl/ir/patterns/expand.py
- src/asdl/ir/patterns/tokenize.py
- src/asdl/ir/patterns/diagnostics.py
- tests/unit_tests/ir (new pattern engine tests)

## References
- agents/scratchpads/architect_scratchpad.md
- ADR-0009
- ADR-0011
- ADR-0012
- ADR-0013
- docs/specs/spec_asdl_pattern_expansion.md
