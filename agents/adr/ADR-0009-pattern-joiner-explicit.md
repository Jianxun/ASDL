Title: ADR-0009: Explicit Pattern Concatenation (No Implicit Joiner)
Status: Accepted

## Context
Current pattern expansion inserts an implicit `_` between literal prefixes and
expanded suffixes. This yields awkward results for parameters (e.g., `m=<1|2>`
expands to `m=_1`), and forces authors to work around an implicit join rule.

## Decision
Remove implicit joiner insertion. Pattern expansion is **literal concatenation**
of tokens; any join character must be authored explicitly.

Examples:
- `DATA[3:0]` -> `DATA3 DATA2 DATA1 DATA0`
- `OUT<P|N>` -> `OUTP OUTN`
- `OUT_<P|N>` -> `OUT_P OUT_N`
- `m=<1|2>` -> `m=1 m=2`

This applies uniformly to enum and range expansion and to mixed literal/group
segments.

## Consequences
- Breaking change for existing pattern expectations and tests.
- Specs and examples must include explicit separators where desired.
- Pattern elaboration and verification remain otherwise unchanged.

## Alternatives
- Keep implicit `_`. Rejected: produces surprising outputs for param values.
- Conditional joiner based on prefix suffix classes. Rejected: hidden rules and
  increased ambiguity.
