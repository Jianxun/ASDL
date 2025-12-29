# Contract

## Project overview
ASDL (Analog Structured Description Language) is a Python framework for analog circuit design: parse YAML ASDL, elaborate/validate, and emit SPICE/netlist artifacts. A major refactor is underway to adopt xDSL as the single semantic core while keeping ruamel+pydantic as front-end shape gate.

## System boundaries / components
- CLI and tooling under `src/asdl/` (parser, elaborator, validator, generator, import system, diagnostics).
- xDSL refactor work tracked via `agents/context` and `agents/scratchpads/` (e.g., `xDSL_refactor.md`).
- Docs under `doc/`; examples under `examples/`; tests under `tests/`.
- Visualization prototypes under `prototype/visualizer_react_flow/` (React Flow) and `prototype/visualization/` (jsPlumb legacy).
- Context/state under `agents/context`; roles under `agents/roles`; ADRs under `agents/adr/`.
- Legacy todos in `context/todo_*.md` are frozen pre-xDSL; new tasks will live in `agents/context/tasks.md`.

## Interfaces & data contracts
- `agents/context/contract.md` maintains this structure; keep sections current.
- `agents/context/tasks.md`: single task board with IDs `T-00X`, status, owner, DoD, verify commands, links, and subsystem tags when relevant. `tasks_archived.md` holds completed items.
- `agents/context/handoff.md`: succinct current state, last verified status, next 1–3 steps, risks.
- `agents/context/codebase_map.md`: navigation reference; update when files move or new subsystems appear.
- `agents/context/lessons.md`: durable lessons/best practices; ADRs go in `agents/adr/` and are referenced here.
- Ordering rule for schema: if order matters, model as YAML lists; uniqueness is enforced by verification passes, not by dict key uniqueness.

## Invariants
- xDSL is the single source of semantic truth; pydantic is a shape/type gate only.
- Preserve declared port/pin ordering end-to-end (AST → IR → SPICE); deterministic outputs.
- Lowering must not crash on bad designs; verifiers/passes emit diagnostics instead.
- Use project venv at `venv/` for all commands/tests.
- Keep contract/map/tasks/handoff aligned with repository reality; update after merges or major decisions.
- Legacy `context/todo_*.md` remain unchanged until explicitly migrated.

## Verification protocol
- Manual check: `agents/context` contains lessons.md, contract.md, tasks.md, handoff.md, tasks_archived.md, codebase_map.md.
- Spot-check that contract reflects current architecture (xDSL core, ordering-as-lists rule) and that codebase_map lists active subsystems.

## Decision log
- 2025-12-28: xDSL refactor adopted layered stack (ruamel → formatter → pydantic shape gate → lowering → xDSL semantic core → passes/emit); semantic meaning lives only in xDSL.
- 2025-12-28: For any ordered data, use YAML lists; uniqueness enforced by verification passes (no reliance on dict order/keys).
- 2025-12-28: ADR-0001 — Superseded by `spec_ast.md` / `spec_asdl_ir.md`; canonical v0 view kinds are `{subckt, subckt_ref, primitive, dummy, behav}`, reserved view names are `nominal` (alias `nom`) and `dummy`; dummy restricted to empty or `weak_gnd` in v0; `subckt_ref` assumes identity pin_map when omitted.
- 2025-12-28: ADR-0002 — Pattern expansion and binding semantics: flat ordered lists, left-to-right duplication, named-only binding, strict length rule, scalar-only implicit broadcast, collision and malformed-pattern errors.
- 2025-12-28: ADR-0003 — SelectView compiler pass validates all views post-config/view_order, selects one per module, defaults to `nominal`, reserves `dummy` for blackout; exclusivity enforced by selection not schema.
