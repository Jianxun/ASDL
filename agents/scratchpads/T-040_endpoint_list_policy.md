# T-040 Endpoint List Policy

## Goal
Decide whether YAML list authoring for endpoint lists is supported.

## Notes
- Decision (2026-01-02): if delimiter spec changes to `|` and `;`, endpoint lists become YAML lists only (string form removed).
- Delimiter rules: forbid whitespace around all delimiters; expansion resolves strictly left-to-right by concatenating expanded lists.
- Follow-on: update pattern expansion spec + AST/spec docs and add implementation tasks.

## Files
- docs/specs_mvp/spec_ast_mvp.md
- agents/context/contract.md (decision log)
