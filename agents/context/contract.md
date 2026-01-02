# Contract

## Project overview
ASDL (Analog Structured Description Language) is a Python framework for analog circuit design: parse YAML ASDL, elaborate/validate, and emit SPICE/netlist artifacts. The MVP refactor uses a Pydantic AST with ruamel-based parsing and xDSL dialects for NFIR/IFIR; ngspice emission is the initial backend.

## System boundaries / components
- Active refactor surface under `src/asdl/ast/` and `src/asdl/ir/`; other pipeline modules are archived under `legacy/src/asdl/`.
- xDSL refactor work tracked via `agents/context` and `agents/scratchpads/` (e.g., `xDSL_refactor.md`).
- Docs under `docs/`; MVP specs under `docs/specs_mvp/`; full specs under `docs/specs/`.
- Examples under `examples/`; archived tests under `legacy/tests/`.
- Visualization prototypes under `prototype/visualizer_react_flow/` (React Flow) and `prototype/visualization/` (jsPlumb legacy).
- Context/state under `agents/context`; roles under `agents/roles`; ADRs under `agents/adr/`.
- Legacy todos in `context/todo_*.md` are frozen pre-xDSL; new tasks will live in `agents/context/tasks.md`.

## Interfaces & data contracts
- `agents/context/contract.md` maintains this structure; keep sections current.
- `agents/context/okrs.md`: current OKRs; `agents/context/tasks.md` references these goals.
- `agents/context/tasks.md`: single task board with IDs `T-00X`, status, owner, DoD, verify commands, links, and subsystem tags when relevant. `tasks_archived.md` holds completed items.
- `agents/context/handoff.md`: succinct current state, last verified status, next 1-3 steps, risks.
- `agents/context/codebase_map.md`: navigation reference; update when files move or new subsystems appear.
- `agents/context/lessons.md`: durable lessons/best practices; ADRs go in `agents/adr/` and are referenced here.
- Net-first authoring uses YAML map order for `nets:` when order matters, including port order from `$`-prefixed net keys; the parser must preserve source order. Internal IR uses explicit lists; uniqueness is enforced by verification passes, not by dict key uniqueness.
- Diagnostic schema is centralized (code, severity, message, primary span, labels, notes, help, fix-its, source); locations use file + line/col spans; all pipeline stages emit diagnostics via this contract.

## Invariants
- xDSL is the single source of semantic truth; pydantic is a shape/type gate only.
- Preserve declared port/pin ordering end-to-end (AST -> NFIR -> IFIR -> emit); deterministic outputs.
- Lowering must not crash on bad designs; verifiers/passes emit diagnostics instead.
- No user-facing errors via raw exceptions; emit diagnostics through the shared diagnostic core.
- Instance params must not introduce new device params; emit a warning and ignore unknown keys.
- Use project venv at `venv/` for all commands/tests.
- Keep contract/map/tasks/handoff aligned with repository reality; update after merges or major decisions.
- Legacy `context/todo_*.md` remain unchanged until explicitly migrated.

## Verification protocol
- Manual check: `agents/context` contains lessons.md, contract.md, okrs.md, tasks.md, handoff.md, tasks_archived.md, codebase_map.md.
- Spot-check that contract reflects current architecture (AST -> NFIR -> IFIR -> emit, ordering-as-lists rule) and that codebase_map lists active subsystems.

## Decision log
- 2026-01-01: Net-first authoring schema infers ports only from `$`-prefixed net keys in `nets:`; inline pin bindings never create ports. Port order follows YAML source order of `$` nets. LHS `*` is invalid without an explicit domain (`<...>` or `[...]`).
- 2025-12-28: xDSL refactor adopted layered stack (ruamel -> formatter -> pydantic shape gate -> lowering -> xDSL semantic core -> passes/emit); semantic meaning lives only in xDSL.
- 2025-12-28: For any ordered data, use YAML lists; uniqueness enforced by verification passes (no reliance on dict order/keys).
- 2025-12-28: ADR-0001 -- Superseded by `docs/specs/spec_ast.md` / `docs/specs/spec_asdl_cir.md`; canonical v0 view kinds are `{subckt, subckt_ref, primitive, dummy, behav}`, reserved view names are `nominal` (alias `nom`) and `dummy`; dummy restricted to empty or `weak_gnd` in v0; `subckt_ref` assumes identity pin_map when omitted.
- 2025-12-28: ADR-0002 -- Pattern expansion and binding semantics: flat ordered lists, left-to-right duplication, named-only binding, strict length rule, scalar-only implicit broadcast, collision and malformed-pattern errors.
- 2025-12-28: ADR-0003 -- SelectView compiler pass validates all views post-config/view_order, selects one per module, defaults to `nominal`, reserves `dummy` for blackout; exclusivity enforced by selection not schema.
- 2026-01-01: ADR-0004 -- ASDL_NLIR uses a single `asdl_nlir` dialect with explicit `elab_state` ("u"/"e"); ASDL_NLIR_U/E remain semantic IR IDs.
- 2025-12-29: Approved clean rewrite: Pydantic v2 AST with locatable diagnostics (ruamel LocationIndex) and no backward-compatibility constraints before MVP.
- 2025-12-30: Archived all non-AST code/tests under `legacy/`; active refactor surface is `src/asdl/ast/`.
- 2026-01-01: MVP pipeline set to AST -> NFIR -> IFIR -> ngspice emission; CIR removed for MVP and NLIR renamed to IFIR with instance-first semantics.
