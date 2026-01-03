# T-042 Pattern Expansion Delimiters (Spec Update)

## Goal
Update pattern expansion spec to the new delimiter policy and list-only endpoint authoring.

## Notes
- Delimiters: `|` for alternatives, `;` for splicing.
- No whitespace around delimiters.
- Expansion resolves strictly left-to-right by concatenating expanded lists.
- Endpoint lists become YAML lists only once delimiter change is adopted.
- Add examples that are YAML-friendly (avoid flow-style comma splitting).
 - 2026-01-02: Updated `docs/specs/spec_asdl_pattern_expansion.md` to remove whitespace around delimiters and tighten rules.

## Files
- docs/specs/spec_asdl_pattern_expansion.md
- docs/specs/spec_ast.md
- docs/specs_mvp/spec_ast_mvp.md
