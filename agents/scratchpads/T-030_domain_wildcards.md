# T-030 — Domain Wildcard Sugar (ASDL_A → ASDL_NFIR)

## Goal
Implement domain wildcard sugar in the authoring surface and resolve it during AST→NFIR.

## References
- `docs/v2/asdl_schema_net_first.md`
- `docs/specs/spec_asdl_nfir.md`

## Notes
- Preserve basename + domain representation post-resolution.

## File hints
- `src/asdl/ast/`
- `src/asdl/ir/converter.py`
- `tests/unit_tests/parser/`
