# T-203 Registry plumbing for AtomizedGraph -> IFIR metadata

## Goal
- Add registry support for device backends and per-expression pattern kinds for AtomizedGraph -> IFIR lowering.

## Notes
- Keep core graphs unchanged; registries carry backend templates and pattern kind metadata.
- Cache pattern expressions by (kind, expression) during AST -> PatternedGraph lowering.
- Update builder tests to assert new registries are populated.

## Status
- [ ] Not started
