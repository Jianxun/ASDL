# Handoff

## Current state
- Refactor specs are canonical: `agents/specs/spec_ast.md` (pydantic AST) and `agents/specs/spec_asdl_ir.md` (xDSL IR) supersede ADR-0001 for view kinds (now {subckt, subckt_ref, primitive, dummy, behav}) and tighten dummy/subckt_ref/alias rules.
- ADR-0001 marked superseded; ADR-0002/0003 remain active. Contract updated accordingly.
- Branch `refactor-prep` created; ADR/spec edits committed previously. Current working tree has pending spec/context edits (to commit).
- Direction approved: clean rewrite pre-MVP with Pydantic v2 AST + locatable diagnostics, new xDSL IR; no backward-compatibility constraints.
- Tasks board updated with executor-ready rewrite tasks (T-010..T-015); earlier design tasks superseded.

## Last verified status
- Context files present; specs and ADRs aligned; no automated checks.

## Next steps (1–3)
1. Assign T-010/T-011/T-012 to Executors and kick off implementation in parallel.
2. Decide where the new AST package lives (`src/asdl/ast/` recommended) and update imports once T-010 lands.
3. Plan the sequencing for IR passes (T-013) vs netlist emission (T-014).

## Risks / unknowns
- Legacy `context/todo_*.md` likely stale; avoid mixing with new board until reconciled.
- Dummy default semantics are backend-defined; lock deterministic defaults during implementation.
- Legacy generator/validator depend on old dataclasses; cleanup sequencing matters (T-015).
