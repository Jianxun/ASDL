# T-053 Pattern Expansion

## Context
Pattern expansion per `docs/specs/spec_asdl_pattern_expansion.md` is the next major feature. MVP currently accepts explicit names only; patterns/domains must be expanded before IFIR lowering.

## Notes
- Implement core expansion: numeric ranges, alternation, splicing; expansion order and collision rules.
- Preserve raw pattern tokens verbatim through AST/NFIR/IFIR; avoid basename+pattern decomposition because `;` can introduce multiple basenames.
- Patterns are allowed only in instance names, net names, and endpoint tokens (device name and pin name). Patterns are forbidden in model names.
- Port derivation: `$` nets carry the pattern verbatim; `;` is forbidden in `$` net expressions.
- Literal names may only use `[A-Za-z_][A-Za-z0-9_]*`; delimiters (`<`, `>`, `[`, `]`, `;`) are forbidden in literals.
- Binding guideline: if an instance pattern expands to N instances, every port binding must expand to N nets (either patterned or via explicit repeat).
- Net binding guideline: if the net is scalar, all endpoint patterns bind to it (endpoints may have differing lengths). If the net expands to N, every endpoint must expand to N; bind by index.
- Splicing (`;`) is pure list concatenation; no segment alignment semantics. Binding compares total length only.
- Canonical naming: use `_` between basename and suffixes; individual suffixes are kept for readability.
- Expansion size limit: 10k expanded atoms per token (hard error for now).
- Add unit tests for success cases and error diagnostics.

## DoD
- AST/NFIR/IFIR retain raw pattern tokens until elaboration.
- Tests cover round-trip preservation of patterned tokens.
