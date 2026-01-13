# Spec - Pipeline Orchestration v0

## Purpose
Define the canonical compiler pipeline orchestration, pass boundaries, and
entrypoint for the xDSL-based flow. This spec supersedes the MVP pipeline notes.

## Scope
- Input: validated AST (`AsdlDocument`) with import resolution already complete
  (ProgramDB + NameEnv).
- Output: GraphIR `graphir.program` ready for optional IFIR projection.
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
- Returns `None` on fatal errors (e.g., AST->NFIR conversion failures), along
  with diagnostics.
- Does not raise user-facing exceptions; all user-visible failures are
  diagnostics.

## Pre-pipeline stage (required)
1. Import resolution
   - Build ProgramDB and per-file NameEnv from the entry document and its
     imports.
   - Resolve symbol identities to `(file_id, name)` before AST->NFIR.

## Pipeline stages
1. AST -> NFIR conversion
   - Use `convert_document` from `src/asdl/ir/converters/ast_to_nfir.py`.
   - On error, return `None` + diagnostics without continuing.
2. NFIR -> GraphIR pass pipeline (xDSL PassManager)
   - Wrap the NFIR `DesignOp` in a `builtin.module` for the pass manager.
   - Run passes in the order below.
3. GraphIR output (pipeline return)
   - Return `graphir.program`; GraphIR remains the canonical IR for semantics.

## Pass order (NFIR -> GraphIR)
```
VerifyNfirPass (optional, gated by verify)
PatternExpandPass (required)
NfirToGraphirPass (required)
VerifyGraphirPass (optional, gated by verify)
```

Pass requirements:
- `PatternExpandPass` expands tokens into ordered atom lists and emits bundle
  and pattern-expression metadata (no inference).
- `NfirToGraphirPass` must replace the `asdl_nfir.design` op with a
  `graphir.program` op in the module body.
- Verify passes must use xDSL verifiers (or equivalent invariant checks) and
  emit diagnostics instead of raising user-facing exceptions.

## Projections and emission (outside pipeline)
- GraphIR -> IFIR projection is a separate step used for backend emission.
- Use `emit_netlist` from `src/asdl/emit/netlist.py`.

## Diagnostics and determinism
- Diagnostics are accumulated across all stages and returned in deterministic
  order.
- Output must be deterministic for identical inputs.

## Non-goals
- Import resolution inside the xDSL pass manager.
- Round-trip conversions between stages.
