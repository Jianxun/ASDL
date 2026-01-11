# Spec - MVP Pipeline Orchestration v0

## Purpose
Define the MVP compiler pipeline orchestration, pass boundaries, and entrypoint
for the xDSL-based flow. This spec focuses on wiring and pass ordering, not on
individual dialect semantics.

## Scope
- Input: validated AST (`AsdlDocument`) produced by the parser.
- Output: ASDL_IFIR `DesignOp` ready for netlist emission.
- Emission is a separate step (see `docs/specs_mvp/spec_netlist_emission_mvp.md`).

## Entrypoint
Location: `src/asdl/ir/pipeline.py`

Required entrypoint (name can vary, behavior cannot):
```
run_mvp_pipeline(document: AsdlDocument, *, verify: bool = True)
  -> tuple[DesignOp | None, list[Diagnostic]]
```

Behavior:
- Returns `None` on fatal errors (e.g., AST->NFIR conversion failures), along
  with diagnostics.
- Does not raise user-facing exceptions; all user-visible failures are
  diagnostics.

## Pipeline stages (MVP)
1. AST -> NFIR conversion
   - Use `convert_document` from `src/asdl/ir/converters/ast_to_nfir.py`.
   - On error, return `None` + diagnostics without continuing.
2. NFIR -> IFIR pass pipeline (xDSL PassManager)
   - Wrap the NFIR `DesignOp` in a `builtin.module` for the pass manager.
   - Run passes in the order below.
3. Emission (outside pipeline)
   - Use `emit_netlist` from `src/asdl/emit/netlist.py`.

## Pass order (NFIR -> IFIR)
```
VerifyNfirPass (optional, gated by verify)
NfirToIfirPass (required)
PatternAtomizePass (required)
VerifyIfirPass (optional, gated by verify)
```

Pass requirements:
- `NfirToIfirPass` must replace the `asdl_nfir.design` op with an
  `asdl_ifir.design` op in the module body.
- `PatternAtomizePass` expands multi-atom patterns into single-atom patterns,
  validates literal-name collisions, and ensures endpoint atoms map to declared
  instance atoms.
- Verify passes must use xDSL verifiers (or equivalent invariant checks) and
  emit diagnostics instead of raising user-facing exceptions.

## Diagnostics and determinism
- Diagnostics are accumulated across all stages and returned in deterministic
  order.
- Output must be deterministic for identical inputs.

## Non-goals
- Round-trip conversions between stages.
- Import resolution or AST elaboration inside the xDSL pass manager (handled
  prior to AST->NFIR in the MVP flow).
