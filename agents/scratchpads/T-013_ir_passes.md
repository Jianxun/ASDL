# T-013 — IR Passes (Link/Resolve, SelectView)

## Goal
Implement core IR passes: alias expansion, link/resolve, and SelectView.

## References
- `docs/specs/spec_asdl_cir.md`

## Notes
- Enforce default `nominal` view selection and dummy name/kind coupling.
- Emit diagnostics for unresolved symbols/aliases and invalid view selections.

## File hints
- `src/asdl/ir/` (new passes folder if needed)
- `tests/unit_tests/passes/`
