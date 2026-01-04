# T-058 Pattern Binding Verification

## Context
Binding rules for patterned nets/endpoints must be enforced before elaboration. Patterns are flattened to a single list for length comparisons; no segment alignment semantics.

## Notes
- If net is scalar: all endpoint patterns bind to it (endpoints may have differing lengths).
- If net expands to N: all endpoints must expand to N; bind by index.
- Bindings compare the string form of fully expanded tokens (e.g., `MN<A,B>` matches `MN_A` and `MN_B`).
- Use a shared equivalence helper in both binding verification and elaboration.
- Every scalar endpoint (post-expansion element) binds to exactly one net.
- Emit diagnostics on mismatch or malformed patterns.

## DoD
- Verification rules implemented in IR layer with unit tests.
- Clear diagnostics for length mismatches and invalid patterns.
