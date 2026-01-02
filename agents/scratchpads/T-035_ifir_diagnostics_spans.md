# T-035 - IFIR conversion diagnostics spans

## Task summary
DoD:
- Decide how to map NFIR `src`/AST locations into IFIR conversion diagnostics.
- Add span-aware diagnostics (or document why spans are unavailable) for NFIR->IFIR conversion errors.
- Extend unit tests to cover diagnostics location behavior as needed.

Verify:
- `pytest tests/unit_tests/ir`
