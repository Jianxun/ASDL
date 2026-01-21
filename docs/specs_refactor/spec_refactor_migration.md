# Refactor Spec - Migration Plan

Status: Draft (refactor-only; not canonical)

## Purpose
Document the phased migration that keeps the legacy xDSL pipeline functional
while the new dataclass-based core is implemented in parallel.

## Phases
### Phase 0 - Freeze interfaces and specs
- Lock PatternedGraph, registries, and pattern service APIs.
- Keep existing AST->GraphIR entrypoints and diagnostics flow unchanged.

### Phase 1 - Build core + pattern service (no CLI changes)
- Implement dataclass PatternedGraph + registries + GraphIndex.
- Implement pattern parsing/binding/expansion as pure functions with tests.

### Phase 2 - New lowering path (side-by-side)
- AST -> GraphSeed -> BindingPlan -> PatternedGraph.
- Reuse ID allocation, symbol resolution, and file ordering as-is.
- Add list-of-lists endpoint parsing and schematic hints registry.

### Phase 3 - Compatibility adapter
- PatternedGraph -> atomized GraphIR (or direct emission adapter).
- Verify netlist output parity against legacy path.

### Phase 4 - Opt-in pipeline + parity harness
- Add CLI flag (`--pipeline=core|legacy`).
- Compare diagnostics and outputs on examples/tests; fix diffs.

### Phase 5 - Default flip + deprecate legacy
- Switch default to core once parity is proven.
- Keep legacy behind a flag for a deprecation window.

## Notes
- Diagnostics are returned as data; CLI determines exit codes.
- Legacy pipeline remains the default until parity is verified.
