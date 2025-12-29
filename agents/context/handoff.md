# Handoff

## Current state
- Refactor specs are canonical: `agents/specs/spec_ast.md` (pydantic AST) and `agents/specs/spec_asdl_ir.md` (xDSL IR) supersede ADR-0001 for view kinds (now {subckt, subckt_ref, primitive, dummy, behav}) and tighten dummy/subckt_ref/alias rules.
- ADR-0001 marked superseded; ADR-0002/0003 remain active. Contract updated accordingly.
- Branch `refactor-prep` created; ADR/spec edits committed previously. Current working tree has pending spec/context edits (to commit).
- Tasks board seeded (T-001/T-002 ready; T-003 backlog) for schema/view/spec work; concrete implementation tasks deferred to next session.

## Last verified status
- Context files present; specs and ADRs aligned; no automated checks.

## Next steps (1–3)
1. Commit remaining spec/context changes on `refactor-prep`.
2. In next session, create concrete implementation tasks (schema/pydantic updates, IR dialect scaffolding, SelectView pass, netlist dialect).
3. Consider migrating relevant points from legacy `context/` files into `agents/specs`/ADR if still applicable.

## Risks / unknowns
- Legacy `context/todo_*.md` likely stale; avoid mixing with new board until reconciled.
- Dummy default semantics are backend-defined; ensure we lock a deterministic default during implementation.

