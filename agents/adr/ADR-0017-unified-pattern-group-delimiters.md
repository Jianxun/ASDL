# ADR-0017: Unified Pattern Group Delimiters

Status: Proposed

## Context
Numeric range patterns currently use `[...]`, while literal enums use `<...>`.
This conflicts with YAML flow-style lists in endpoint lists and makes authoring
fragile. We want a single group delimiter that is YAML-friendly while preserving
first-class pattern semantics for downstream tools.

## Decision
- Use `<...>` for both literal enums and numeric ranges.
- Literal enums use `|` (unchanged): `<a|b|c>`.
- Numeric ranges use a single `:` with integer bounds: `<25:1>`.
- A group with neither `|` nor `:` is a single-alternative enum, even if it is
  digits (e.g., `<25>` is literal `"25"`).
- `<@name>` remains the named-pattern reference token.
- Mixing `|` and `:` inside a single group is invalid; multiple `:` are invalid.
- Pattern provenance remains typed: GraphIR `pattern_parts` stays `list[str|int]`.
  Numeric ranges produce integer parts; enums produce string parts.
- Binding/identity semantics remain based on expanded atom strings; typed parts
  are provenance for downstream tools only.

## Consequences
- Breaking change: `[...]` numeric ranges are removed; all docs/examples/parser
  logic must update to `<start:end>`.
- YAML flow endpoint lists no longer collide with range syntax.
- Tooling that assumes `[]` ranges must be updated (parser, expander, syntax
  highlighter, tests, and examples).
- Downstream tools can still derive numeric semantics from `pattern_parts`
  without re-parsing raw strings.
- Post-MVP: step ranges like `<start:step:end>` are deferred; no implicit
  defaults or parity shortcuts are introduced in MVP.

## Alternatives
- Keep `[]` and require block lists/quoting in YAML: rejected as ergonomically
  brittle.
- Support both `[]` and `<:>`: rejected to avoid dual syntax and ambiguity.
- Infer numeric intent from basenames or coerce digit-only enums to integers:
  rejected due to non-local semantics and loss of literal numeric enums.
