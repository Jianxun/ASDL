# T-056 Exports Sugar

## Context
Port export/forwarding is authoring sugar in `docs/specs/spec_ast.md`. It can be implemented after core features.

## Notes
- Add `exports` to AST module schema.
- Expand exports into nets before NFIR/IFIR lowering.
- Add diagnostics for invalid module references or port conflicts.

## DoD
- `exports` supported end-to-end as sugar.
- Tests cover forwarding, collisions, and invalid references.
