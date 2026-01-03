# ADR-0005: Pattern Delimiters and Endpoint List Authoring

Status: Accepted

## Context
ASDL endpoint lists and pattern expansion syntax need to be YAML-friendly and
unambiguous. The previous delimiter choice used commas inside `<...>` patterns,
which conflicts with YAML flow-style parsing and encourages quoting or awkward
formatting. Upcoming bundle/splice syntax also benefits from clear, simple
separators.

## Decision
- Use `|` as the literal enumeration delimiter inside `<...>`.
- Use `;` as the splice/concatenation delimiter between segments.
- Forbid whitespace around all delimiters (`|` and `;`).
- Resolve cascaded patterns strictly left-to-right by concatenating expanded
  lists.
- If the delimiter change is adopted, endpoint lists become YAML lists only
  (string form removed).

## Consequences
- Breaking change for authoring: endpoint lists must be YAML lists of strings.
- Specs and parser/AST schema must be updated to reflect list-only endpoints.
- Examples must avoid whitespace around delimiters and document the new rules.

## Alternatives
- Keep comma delimiters and rely on quoting: rejected due to YAML friction and
  authoring errors.
- Allow optional whitespace around delimiters: rejected to avoid ambiguity and
  inconsistent parsing.
- Keep string-only endpoint lists: rejected once delimiter change is adopted to
  reduce YAML parsing pitfalls.
