# Refactor Spec - Compiler Stack and API Boundaries

Status: Draft (refactor-only; not canonical)

## 1. Purpose
Define the refactor target compiler stack that preserves the current pipeline
while introducing a dataclass-based core and a programmatic API.

## 2. Design Goals
- Keep the legacy pipeline functional during migration.
- Provide a clean API for programmatic tooling (queries, emission, visualization).
- Isolate pattern semantics in a dedicated service.
- Maintain deterministic outputs and diagnostics parity.

## 3. Refactor Stack (Proposed)
The new stack runs in parallel to the legacy xDSL path.

```
ASDL YAML
  -> AST (pydantic, validated)
  -> import resolution (ProgramDB + NameEnv)
  -> PatternExpressionRegistry
  -> GraphSeed (structural graph with expr refs)
  -> BindingPlan (pattern service)
  -> PatternedGraph (dataclass core + registries)
  -> AtomizedGraph (derived, optional)
  -> emission backend
```

Notes:
- PatternedGraph is the canonical API model.
- AtomizedGraph is a derived view used for emission and legacy compatibility.
- Diagnostics are collected at each stage and returned as data.

## 4. Legacy Compatibility
The existing xDSL GraphIR pipeline remains the default until parity is proven.
The new pipeline is opt-in (CLI flag or API entrypoint).

## 5. API Boundaries
CLI is a thin wrapper around the API; no CLI-only logic.

Suggested API surface:
- `load_ast(path | text) -> AstBundle`
- `resolve_imports(ast, config) -> ProgramDb`
- `build_patterned_graph(ast, program_db) -> GraphBundle`
- `verify_graph(graph_bundle) -> list[Diagnostic]`
- `emit_netlist(graph_bundle, backend, config) -> EmitResult`
- `query(graph_bundle) -> DesignQuery`

All APIs accept explicit config and return diagnostics rather than raising.

## 6. Migration Expectations
- New verifiers and emit adapters must match legacy netlist output for parity.
- Diagnostic codes and spans should be preserved where possible.
- Legacy pipeline remains available behind a flag until adoption is complete.
