# T-055 Specs Reconciliation

## Context
The MVP pipeline AST -> NFIR -> IFIR -> emit supersedes the older CIR/NLIR staging. Specs in `docs/specs/` must reflect this.

## Notes
- Update or deprecate `spec_asdl_cir.md` and `spec_asdl_nlir.md` to align with IFIR.
- Update `spec_compiler_stack.md` to reflect the canonical pipeline.
- Note the NLIR+CIR merge into IFIR explicitly.

## DoD
- `docs/specs/` reconciled with MVP pipeline.
- Compiler stack spec updated; legacy staging marked as superseded.
