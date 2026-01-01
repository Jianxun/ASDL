# T-032 — Inline Pin-Bind + Suffix Sugar

## Goal
Support inline pin-binding and suffix blocks in ASDL_A and lower into explicit nets/instances.

## References
- `docs/v2/asdl_schema_net_first.md`

## Notes
- Inline binds never create ports; `$` nets must appear in `nets:`.

## File hints
- `src/asdl/ast/`
- `tests/unit_tests/parser/`
