# Spec - Pipeline Orchestration v0

## Purpose
Define the canonical compiler pipeline orchestration, pass boundaries, and
entrypoint for the xDSL-based flow. This spec supersedes the MVP pipeline notes.
GraphIR is the canonical IR; NFIR is projection-only for roundtrip/debugging.

## Scope
- Input: validated AST (`AsdlDocument`) with import resolution already complete
  (ProgramDB + NameEnv).
- Output: GraphIR `graphir.program` plus optional IFIR projection for emission.
- Emission is a separate step (see `docs/specs/spec_netlist_emission.md`).

## Entrypoint
Location: `src/asdl/ir/pipeline.py`

Required entrypoint (name can vary, behavior cannot):
```
compile_to_graphir(
  document: AsdlDocument,
  program_db: ProgramDB,
  name_env: NameEnv,
  *,
  verify: bool = True,
) -> tuple[GraphIrProgramOp | None, list[Diagnostic]]
```

Behavior:
- Entrypoints may accept a resolved wrapper type; the required inputs are the
  entry `AsdlDocument` plus `ProgramDB` and `NameEnv`.
- Returns `None` on fatal errors (e.g., AST->GraphIR conversion failures), along
  with diagnostics.
- Does not raise user-facing exceptions; all user-visible failures are
  diagnostics.

## Pre-pipeline stage (required)
1. Import resolution
   - Build ProgramDB and per-file NameEnv from the entry document and its
     imports.
   - Resolve symbol identities to `(file_id, name)` before AST->GraphIR.

## Pipeline stages
1. AST -> GraphIR conversion
   - Use `convert_document` or `convert_import_graph` from
     `src/asdl/ir/converters/ast_to_graphir.py`.
   - On error, return `None` + diagnostics without continuing.
2. GraphIR -> IFIR projection (optional, for emission)
   - Wrap the `graphir.program` in a `builtin.module` for the pass manager.
   - Run passes in the order below.
3. IFIR output (projection return)
   - Return `ifir.design` when projection runs; GraphIR remains the canonical
     semantic IR.

## Pass order (GraphIR -> IFIR)
```
VerifyGraphirPass (optional, gated by verify)
GraphirToIfirPass (required)
AtomizeIfirPass (required)
VerifyIfirPass (optional, gated by verify)
```

Pass requirements:
- `GraphirToIfirPass` must replace the `graphir.program` op with an
  `ifir.design` op in the module body.
- `AtomizeIfirPass` expands patterns into atomized IFIR and preserves
  `pattern_origin` metadata.
- Verify passes must use xDSL verifiers (or equivalent invariant checks) and
  emit diagnostics instead of raising user-facing exceptions.

## Projections and emission (outside pipeline)
- NFIR is a projection-only IR used for roundtrip/debugging, not a pipeline
  stage.
- Use `emit_netlist` from `src/asdl/emit/netlist.py` after IFIR projection.

## Diagnostics and determinism
- Diagnostics are accumulated across all stages and returned in deterministic
  order.
- Output must be deterministic for identical inputs.

## Non-goals
- Import resolution inside the xDSL pass manager.
- Round-trip conversions between stages.
