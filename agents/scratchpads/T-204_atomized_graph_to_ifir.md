# T-204 AtomizedGraph -> IFIR lowering pass

## Goal
- Implement AtomizedGraph -> IFIR lowering using registry-backed pattern tables and backend templates.

## Notes
- Build IFIR design/modules/nets/instances/devices from AtomizedGraph + registries.
- Emit diagnostics for missing/invalid registry data and unresolved references.
- Add tests for a happy path and missing-registry diagnostics.

## Status
- [ ] Not started
