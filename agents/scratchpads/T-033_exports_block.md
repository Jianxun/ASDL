# T-033 — Exports Block Lowering

## Goal
Implement `exports:` lowering into `$` nets with conflict checks.

## References
- `docs/v2/asdl_schema_net_first.md`

## Notes
- Preserve port order: explicit `$` nets first, then forwarded exports.

## File hints
- `src/asdl/ast/`
- `src/asdl/ir/converter.py`
- `tests/unit_tests/parser/`
