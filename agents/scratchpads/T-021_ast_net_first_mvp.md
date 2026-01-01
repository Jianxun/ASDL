# T-021 — ASDL_A Net-First AST MVP

## Goal
Rewrite Tier-1 AST + parser for explicit net-first schema (instances/nets only) per MVP scope.

## References
- `docs/specs/spec_compiler_stack.md`
- `docs/v2/asdl_schema_net_first.md`

## Notes
- No pattern sugar, imports, exports, or inline pin-bind sugar in MVP.
- Ports are inferred only from `$` net keys; port order follows source order.

## File hints
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `tests/unit_tests/parser/`
