# Contract

## Project overview
ASDL (Analog Structured Description Language) is a Python framework for analog circuit design: parse YAML ASDL, elaborate/validate, and emit SPICE/netlist artifacts. The MVP refactor uses a Pydantic AST with ruamel-based parsing and xDSL dialects for NFIR/IFIR; ngspice emission is the initial backend. The MVP pipeline (AST -> NFIR -> IFIR -> emit) supersedes older main spec staging and will be reconciled in `docs/specs/`.

## System boundaries / components
- Active refactor surface under `src/asdl/ast/` and `src/asdl/ir/`; other pipeline modules are archived under `legacy/src/asdl/`.
- xDSL refactor work tracked via `agents/context` and `agents/scratchpads/` (e.g., `T-030_ast_parser_mvp.md`).
- Docs under `docs/`; MVP specs under `docs/specs_mvp/`; full specs under `docs/specs/`.
- Examples under `examples/`; archived tests under `legacy/tests/`.
- Visualization prototypes under `prototype/visualizer_react_flow/` (React Flow) and `prototype/visualization/` (jsPlumb legacy).
- Context/state under `agents/context`; roles under `agents/roles`; ADRs under `agents/adr/`.
- Legacy todos in `context/todo_*.md` are frozen pre-xDSL; new tasks live in `agents/context/tasks.yaml` (status in `agents/context/tasks_state.yaml`).

## Interfaces & data contracts
- `agents/context/contract.md` maintains this structure; keep sections current.
- `agents/context/tasks.yaml`: active task cards (current_sprint/backlog) without status fields; tasks may include optional `depends_on` lists of `T-00X`.
- `agents/context/tasks_state.yaml`: per-task state map (`status`, `pr`, `merged`) for active tasks; `pr` is a non-negative integer PR number or null; edited by Architect, Reviewer, and Executor.
- `agents/context/tasks_icebox.yaml`: deferred task cards (icebox).
- `agents/context/tasks_archived.yaml`: archived done tasks; one-line entries keyed by task id (suffix allowed for historical duplicates) with `completed_on`, `owner`, `scratchpad`, and `pr`.
- `agents/context/tasks_archived.md`: legacy snapshot (read-only).
- `agents/context/project_status.md`: project status, last verified status, next 1-3 steps, risks; updated by Architect.
- `agents/context/codebase_map.md`: navigation reference; update when files move or new subsystems appear.
- `agents/context/lessons.md`: durable lessons/best practices; ADRs go in `agents/adr/` and are referenced here.
- Netlist emission uses backend names (e.g., `sim.ngspice`) as stable identifiers in CLI and config; the CLI exposes `--backend` with default `sim.ngspice`.
- Backend config schema (`config/backends.yaml` or `ASDL_BACKEND_CONFIG`) must include per-backend `templates`, `extension` (verbatim output suffix), and `comment_prefix`.
- Net-first authoring uses YAML map order for `nets:` when order matters; port order derives from `$`-prefixed net keys in `nets` first, then `$`-prefixed nets first-seen in `instance_defaults` bindings (deterministic order). The parser must preserve source order. Internal IR uses explicit lists; uniqueness is enforced by verification passes, not by dict key uniqueness.
- Diagnostic schema is centralized (code, severity, message, primary span, labels, notes, help, fix-its, source); locations use file + line/col spans; all pipeline stages emit diagnostics via this contract.
- AST->NFIR converter returns `(DesignOp | None, diagnostics)`; invalid instance or endpoint tokens emit `IR-001`/`IR-002` with `Severity.ERROR` and return `None`.

## Invariants
- xDSL is the single source of semantic truth; pydantic is a shape/type gate only.
- Preserve declared port/pin ordering end-to-end (AST -> NFIR -> IFIR -> emit); deterministic outputs.
- Lowering must not crash on bad designs; verifiers/passes emit diagnostics instead.
- No user-facing errors via raw exceptions; emit diagnostics through the shared diagnostic core.
- Converters MUST NOT silently drop endpoints, connections, or nets; any missing references must emit diagnostics.
- Converters MUST NOT raise `ValueError` for malformed IR; emit diagnostics and return failure indicators instead.
- Instance params must not introduce new device params; emit a warning and ignore unknown keys.
- System device names (prefixed `__`) are reserved; regular device names MUST NOT use this prefix.
- Backend config file MUST define all required system devices; missing required system devices emit `MISSING_BACKEND` error and abort emission.
- When `top_as_subckt` is false, netlist emission MUST NOT emit any top-level subckt wrapper lines.
- Backend config location determined by `ASDL_BACKEND_CONFIG` env var; defaults to `config/backends.yaml`.
- Use project venv at `venv/` for all commands/tests.
- Keep contract/map/tasks/project_status aligned with repository reality; update after merges or major decisions.
- Task cards MUST target a single subsystem/layer, list <= 5 likely files, and include one primary verify command; split cross-cutting or multi-rule work into separate tasks.
- Only the Architect edits task cards/archives (`agents/context/tasks.yaml`, `agents/context/tasks_icebox.yaml`, `agents/context/tasks_archived.yaml`).
- Architect, Reviewer, and Executor may edit `agents/context/tasks_state.yaml` for status/PR/merge changes only.
- Executors update only `agents/scratchpads/T-00X.md` and `agents/context/tasks_state.yaml` (status/PR/merge fields) for their task; they do not edit task cards or project status.
- Explorers update only `agents/scratchpads/T-00X.md` and do not edit task cards, project status, or `agents/context/tasks_state.yaml`.
- Task state gating: review/done statuses require `pr` set to a positive integer; `done` requires `merged` true; early statuses require `pr: null` and `merged: false`.
- `agents/context/project_status.md` is updated only by the Architect.
- Legacy `context/todo_*.md` remain unchanged until explicitly migrated.
- Architect direct-to-main is allowed only for commits that touch files under `agents/` and/or `docs/` exclusively; all other changes require a PR.

## Verification protocol
- Manual check: `agents/context` contains lessons.md, contract.md, tasks.yaml, tasks_state.yaml, tasks_icebox.yaml, tasks_archived.yaml, project_status.md, codebase_map.md.
- Spot-check that contract reflects current architecture (AST -> NFIR -> IFIR -> emit, ordering-as-lists rule) and that codebase_map lists active subsystems.

## Decision log
- 2026-01-01: Net-first authoring schema infers ports only from `$`-prefixed net keys in `nets:`; inline pin bindings never create ports. Port order follows YAML source order of `$` nets. LHS `*` is invalid without an explicit domain (`<...>` or `[...]`). (Superseded 2026-01-11)
- 2026-01-11: Inline pin bindings may introduce `$`-prefixed nets, which create ports if not already declared in `nets:`. Port order is `$` nets from `nets` first, then `$` nets first-seen in inline bindings. Rationale: avoid declaring ports solely for hierarchy wiring. Migration: remove `$` prefix in inline bindings to keep nets internal; or keep ports explicit in `nets` to control order. (Superseded 2026-01-12, ADR-0007)
- 2026-01-12: ADR-0007 -- Inline pin bindings are removed in favor of `instance_defaults`. Defaults apply per instance `ref`; explicit `nets` bindings override defaults and emit warnings unless suppressed by `!inst.pin`. `$` nets introduced by defaults create ports after explicit `$` nets.
- 2026-01-12: ADR-0008 -- Module-local named patterns use `<@name>` and expand via macro substitution prior to AST->NFIR. Named patterns are group tokens only and do not recurse.
- 2026-01-12: ADR-0009 -- Pattern expansion uses explicit concatenation with no implicit joiner; authors include separators explicitly (breaking change; implementation pending).
- 2026-01-12: ADR-0010 -- Patterned instance parameters expand after instance-name expansion; scalar values broadcast and length-`N` values zip by instance index (no cross-product).
- 2025-12-28: xDSL refactor adopted layered stack (ruamel -> formatter -> pydantic shape gate -> lowering -> xDSL semantic core -> passes/emit); semantic meaning lives only in xDSL.
- 2025-12-28: For any ordered data, use YAML lists; uniqueness enforced by verification passes (no reliance on dict order/keys).
- 2025-12-28: ADR-0001 -- Superseded by `docs/specs/spec_ast.md` / `docs/specs/spec_asdl_cir.md`; canonical v0 view kinds are `{subckt, subckt_ref, primitive, dummy, behav}`, reserved view names are `nominal` (alias `nom`) and `dummy`; dummy restricted to empty or `weak_gnd` in v0; `subckt_ref` assumes identity pin_map when omitted.
- 2025-12-28: ADR-0002 -- Pattern expansion and binding semantics: flat ordered lists, left-to-right duplication, named-only binding, strict length rule, scalar-only implicit broadcast, collision and malformed-pattern errors.
- 2025-12-28: ADR-0003 -- SelectView compiler pass validates all views post-config/view_order, selects one per module, defaults to `nominal`, reserves `dummy` for blackout; exclusivity enforced by selection not schema.
- 2026-01-01: ADR-0004 -- ASDL_NLIR uses a single `asdl_nlir` dialect with explicit `elab_state` ("u"/"e"); ASDL_NLIR_U/E remain semantic IR IDs.
- 2025-12-29: Approved clean rewrite: Pydantic v2 AST with locatable diagnostics (ruamel LocationIndex) and no backward-compatibility constraints before MVP.
- 2025-12-30: Archived all non-AST code/tests under `legacy/`; active refactor surface is `src/asdl/ast/`.
- 2026-01-01: MVP pipeline set to AST -> NFIR -> IFIR -> ngspice emission; CIR removed for MVP and NLIR renamed to IFIR with instance-first semantics.
- 2026-01-02: Netlist template placeholders: hard switch from `{conns}` to `{ports}`; `{ports}` optional; `{params}` deprecated (no reserved-status enforcement). Device `ports` field becomes optional in the AST schema to permit templates that do not use ports.
- 2026-01-03: Individual merged parameter values exposed as template placeholders. Templates can now reference device/backend/instance params directly (e.g., `{L}`, `{W}`, `{NF}`, `{m}`). Backward compat preserved for `{params}` formatted string. Props override params if names collide.
- 2026-01-04: ADR-0006 -- System devices for backend structural templates. System devices (prefixed `__`) define backend-specific structural elements in external `backends.yaml`. Required system devices: `__subckt_header__`, `__subckt_footer__`, `__subckt_call__`, `__netlist_header__`, `__netlist_footer__`. Top module emits no wrapper unless `top_as_subckt` uses `__subckt_header__`/`__subckt_footer__`. Backend config location via `ASDL_BACKEND_CONFIG` env var; defaults to `config/backends.yaml`. Missing required system devices = fatal error.
- 2026-01-02: ADR-0005 -- Pattern expansion uses `|` for alternatives and `;` for splicing; no whitespace around delimiters; left-to-right concatenation. Endpoint lists become YAML lists only once the delimiter change lands.
- 2026-01-05: Netlist emission is backend-selected via CLI `--backend` (default `sim.ngspice`); `config/backends.yaml` includes output `extension` per backend; `emit_ngspice` is removed in favor of a unified netlist emitter.
- 2026-01-06: The canonical pipeline is AST -> NFIR -> IFIR -> emit; prior CIR/NLIR staging is superseded and will be reconciled in `docs/specs/`. NLIR and CIR are merged into IFIR.
- 2026-01-06: Pattern expressions are preserved through AST/NFIR/IFIR; a dedicated elaboration pass expands patterns before backend emission.
- 2026-01-06: Pattern splicing (`;`) is pure list concatenation; binding compares total expansion length only (no segment alignment). Canonical expansion uses `_` between basename and suffixes. (Superseded 2026-01-12, ADR-0009)
- 2026-01-06: Pattern bindings compare the fully expanded string tokens (e.g., `MN<A,B>` binds to `MN_A` and `MN_B`).
- 2026-01-06: Patterns are allowed only on instance names, net names, and endpoint tokens (device + pin); patterns are forbidden in model names. `$` net ports preserve the pattern verbatim and forbid `;`. Literal names are limited to `[A-Za-z_][A-Za-z0-9_]*` (no pattern delimiters). Expansion size is capped at 10k atoms per token (for now).
- 2026-01-06: Binding verification and elaboration must share an equivalence helper; scalar endpoints bind to exactly one net.
- 2026-01-06: NFIR/IFIR carry raw pattern tokens; store `expansion_len` metadata for faster verification. NFIR verification runs before IFIR lowering. Prefer single net ops with patterned names (no eager expansion).
- 2026-01-07: Import spec v0.1: imports resolve to files only (no directory imports, no extension inference). `file_id` is an absolute path with `.`/`..` normalization and no symlink resolution. Unqualified references resolve only within the same file. Multiple namespaces may bind to the same `file_id`. Unused imports emit a warning.
- 2026-01-09: Import resolution forbids shadowing: logical-path resolution errors on multiple matches and reports all candidates in root order (`AST-015`).
- 2026-01-08: `file_id` is the normalized absolute path used for symbol identity `(file_id, name)` and is propagated through NFIR/IFIR. Netlist emission remains template-driven; `{file_id}` is available to system-device templates, with entry `file_id` provided to netlist header/footer.
- 2026-01-08: `top` resolves only within the entry file (no `ns.top`). Same-name modules/devices across files are allowed; same-name within a file is still invalid. Netlist emission must guarantee unique subckt identifiers: if duplicates exist across files, backend templates must include `{file_id}` in subckt headers/calls or emission errors. Import resolution adds `ASDL_LIB_PATH` (PATH-style list) after `-I` roots.
- 2026-01-08: Import diagnostics codes are reserved: `AST-010/011/012/013/014`, `IR-010/011`, `LINT-001` per `docs/specs/spec_asdl_import.md`.
- 2026-01-08: Instance type tokens may be qualified as `ns.symbol`; name resolution splits `ref` + `ref_file_id`. Import paths expand `~` and `$VAR` before resolution; `file_id` is the normalized absolute path. Files must define at least one module or device (import-only documents are invalid).
- 2026-01-08: Netlist emission must auto-disambiguate duplicate module names across files by appending `__{hash8}` where `hash8 = sha1(file_id)[:8]`; emitted names are used for subckt headers/calls and `{top}` placeholders. `{sym_name}`/`{top_sym_name}` expose the original module names to templates.
- 2026-01-10: Import logical-path resolution is simplified to search only CLI `--lib` roots (in order) followed by `ASDL_LIB_PATH`; project-root and `-I` roots are removed from the spec. Relative (`./`/`../`) and absolute paths remain unchanged.
- 2026-01-13: ADR-0011 -- Pattern atomization expands multi-atom tokens into single-atom patterns before IFIR verification/emission, preserves `pattern_origin` metadata, enforces subset-of-atoms endpoint validity, and treats literal-name collisions as fatal errors.
- 2026-01-14: ADR-0012 -- NFIR verification and NFIR->IFIR inversion resolve endpoint instances via atomized literal equivalence, enabling subset endpoint tokens while detecting atomized endpoint collisions.
- 2026-01-14: ADR-0013 -- NFIR->IFIR conversion atomizes endpoints and assigns conns per atom, while PatternAtomizePass is idempotent or skipped for already-atomized IFIR.
