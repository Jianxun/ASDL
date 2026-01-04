# T-057 Pattern Expansion Engine

## Context
Implement the standalone pattern expansion logic per `docs/specs/spec_asdl_pattern_expansion.md`. This should not modify pipeline stages yet.

## Notes
- Support numeric ranges, alternation, and splicing; left-to-right expansion.
- Canonical output uses `_` between basename and suffixes.
- Detect malformed patterns, empty segments, and collisions.
- Enforce expansion size limit (10k atoms per token) with a clear diagnostic.

## DoD
- Expansion engine + tests for core forms and error cases.
- No integration with AST/NFIR/IFIR passes yet.
