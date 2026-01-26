# Contract

## Project overview
ASDL (Analog Structured Description Language) is a Python framework for analog circuit design: parse YAML ASDL, elaborate/validate, and emit SPICE/netlist artifacts. The refactor pipeline uses a Pydantic AST with ruamel-based parsing, a dataclass PatternedGraph core, an AtomizedGraph derived view, and a dataclass NetlistIR emission model. ngspice emission is the initial backend. Legacy xDSL GraphIR/IFIR remain for reference during migration but are being retired from the refactor path.

## System boundaries / components
- Active refactor surface under `src/asdl/ast/`, `src/asdl/core/`, `src/asdl/emit/`, and `src/asdl/lowering/`; legacy xDSL dialects live under `src/asdl/ir/` until retirement. Other pipeline modules are archived under `legacy/src/asdl/`.
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
- Pattern definitions may be strings or `{expr, tag}` objects; `axis_id` derives from `tag` when present, otherwise the pattern name. Tags/axis_id are module-local and drive tagged-axis broadcast binding diagnostics.
- Diagnostic schema is centralized (code, severity, message, primary span, labels, notes, help, fix-its, source); locations use file + line/col spans; all pipeline stages emit diagnostics via this contract.
- Deprecated: AST->NFIR converter returns `(DesignOp | None, diagnostics)`; invalid instance or endpoint tokens emit `IR-001`/`IR-002` with `Severity.ERROR` and return `None`. Retained for legacy/roundtrip use only.
- Legacy CLI exposes `ir-dump` to emit GraphIR/IFIR textual IR (`--ir graphir|ifir`) for reference during migration; the refactor pipeline will provide NetlistIR/PatternedGraph dumps for debugging with deterministic output and stable ordering.
- PatternedGraph serialization is exposed via `asdl.core.dump_patterned_graph` / `patterned_graph_to_jsonable`, producing stable JSON with modules, registries, and spans encoded using the diagnostics span JSON shape.
- CLI adds `patterned-graph-dump` to emit PatternedGraph JSON for refactor inspection/visualization workflows.
- PatternedGraph -> AtomizedGraph conversion produces a core, fully-atomized dataclass graph (nets, instances, endpoints) for stateless verification and emission adapters; verifiers must be pure functions that return diagnostics without mutating inputs.
- AtomizedGraph -> NetlistIR conversion produces the emission-ready dataclass representation; NetlistIR verifiers are pure functions that return diagnostics without mutating inputs.

## Invariants
- The dataclass core is the single source of semantic truth; pydantic is a shape/type gate only.
- PatternedGraph is the canonical semantic core; AtomizedGraph is a derived view; NetlistIR is the emission projection; legacy xDSL GraphIR/IFIR are out of the refactor path.
- Preserve declared port/pin ordering end-to-end (AST -> PatternedGraph -> AtomizedGraph -> NetlistIR -> emit); deterministic outputs.
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
- Task state gating: review/done statuses require `pr` set to a positive integer; `done` requires `merged` true; `backlog`/`ready`/`blocked` require `pr: null` and `merged: false`; `in_progress` allows `pr` null or a positive integer with `merged: false`.
- `agents/context/project_status.md` is updated only by the Architect.
- Legacy `context/todo_*.md` remain unchanged until explicitly migrated.
- Architect direct-to-main is allowed only for commits that touch files under `agents/` and/or `docs/` exclusively; all other changes require a PR.
- Public Python modules/classes/functions and non-trivial private helpers MUST include PEP 257 docstrings using Google-style sections; docstrings capture purpose, inputs/outputs, side effects, and relevant invariants or ordering rules for agent readability.
- Comments MUST explain intent, rationale, or tricky logic (not restate code) and remain accurate; prefer docstrings over inline comments for API-level behavior.

## Verification protocol
- Manual check: `agents/context` contains lessons.md, contract.md, tasks.yaml, tasks_state.yaml, tasks_icebox.yaml, tasks_archived.yaml, project_status.md, codebase_map.md.
- Spot-check that contract reflects current architecture (AST -> GraphIR -> IFIR -> emit; NFIR optional for AST projection; ordering-as-lists rule) and that codebase_map lists active subsystems.

## Decision log
### Active ADRs
- ADR-0002 (Proposed): Pattern expansion/binding uses flat ordered lists, named-only binding, and scalar broadcast rules.
- ADR-0003 (Proposed): SelectView pass validates all views and selects one per module.
- ADR-0004: Single `asdl_nlir` dialect with explicit `elab_state` attribute.
- ADR-0005: Pattern delimiters `|` and `;`; endpoint lists are YAML lists only.
- ADR-0006: Backend structural templates are system devices in backend config.
- ADR-0007: `instance_defaults` replace inline pin bindings; defaults can introduce `$` ports.
- ADR-0008: Module-local named patterns via `<@name>` macro substitution.
- ADR-0009: Pattern expansion uses literal concatenation; no implicit joiner.
- ADR-0010: Patterned instance params expand after instance expansion with broadcast/zip rules.
- ADR-0011: Pattern atomization before IFIR verification; literal collisions are errors.
- ADR-0012: NFIR endpoint resolution uses atomized literal equivalence.
- ADR-0013: NFIR->IFIR conversion atomizes endpoints per instance; atomization pass is idempotent.
- ADR-0014: GraphIR is the canonical semantic core with stable IDs and structured graph ops.
- ADR-0015: GraphIR is atomized-only; pattern provenance uses typed pattern_origin + module attrs table.
- ADR-0016: Variables blocks at module/device/backend scopes; `params` renamed to `parameters`.
- ADR-0017 (Proposed): Unified pattern group delimiters using `<...>` for enums and ranges.
- ADR-0018 (Proposed): Backend pattern rendering policy for numeric parts.
- ADR-0020 (Proposed): Tagged pattern axes for broadcast binding (supersedes ADR-0019).
- ADR-0021 (Proposed): Comment-based docstrings for ASDL docs via YAML comment blocks, inline comments, and section bundles.
- ADR-0022: Net name expressions must not use splice delimiters; split net entries per segment (refactor-only until canonical reconciliation).
- ADR-0023: Core graphs include device definitions; modules/devices use `ports` lists (never None); backend templates stay outside core graphs.
- ADR-0024: Replace IFIR with NetlistIR dataclass model; remove xDSL from the refactor pipeline.
- ADR-0025: Hard decommission xDSL pipeline (remove `ir-dump`, move legacy specs, drop dependency).
- ADR-0026 (Proposed): Store pattern origins on AtomizedGraph entities to avoid reconstruction.
- ADR-0027: ASDL visualizer uses unified symbol schema (modules/devices), grid-only pins with floor-biased placement, top-left instance anchors, center-based hubs, and `asdlc visualizer-dump` via PATH.
- ADR-0028 (Proposed): Project `.asdlrc` discovery from entry-file directory upward with rc-defined env/lib roots.

- 2026-01-24: ADR-0024 -- Replace IFIR with NetlistIR dataclass model; remove xDSL from the refactor pipeline (supersedes ADR-0014).
- 2026-01-23: ADR-0023 -- Core graphs include device definitions; modules/devices use `ports` lists (never None); backend templates stay outside core graphs.
- 2026-01-21: PatternedGraph construction now uses a core builder API; AST lowering lives under `src/asdl/lowering/` instead of `asdl.core`.
- 2026-01-25: ADR-0025 -- Hard decommission xDSL pipeline (remove `ir-dump`, move legacy specs, drop dependency).
- 2026-01-26: ADR-0026 (Proposed) -- Store pattern origins on AtomizedGraph entities to avoid reconstruction.
- 2026-01-26: ADR-0027 -- ASDL visualizer symbol schema, pin placement, layout anchors, and compiler-driven dump.
- 2026-01-26: ADR-0028 (Proposed) -- `.asdlrc` discovery (entry-file dir upward), rc-defined env/lib roots, and config precedence.

- 2026-01-16: ADR-0014 -- GraphIR is the canonical semantic core with stable IDs; GraphIR defines program/module/device/net/instance/endpoint ops and module port_order; IFIR is a projection and NFIR is optional. (Superseded 2026-01-24, ADR-0024)
- 2026-01-17: ADR-0015 -- GraphIR stores only atomized names; pattern provenance is attached to ops via typed pattern_origin pointing to a module attrs expression table; endpoint expressions expand as a whole then split on `.`.
- 2026-01-18: ADR-0016 -- Introduce module/device/backend `variables`, rename `params` to `parameters`, and allow `{var}` substitution in instance params with recursion forbidden.
- 2026-01-18: ADR-0017 -- Unify pattern group delimiters: enums and numeric ranges use `<...>` with `|` or `:`; ranges emit integer pattern parts and enums emit strings.
- 2026-01-18: ADR-0018 -- Add backend pattern rendering policies to format numeric pattern parts (e.g., bracketed indices) during emission.
- 2026-01-18: ADR-0019 -- Allow explicit named-pattern broadcast binding when net axes are a subset of endpoint axes.
- 2026-01-20: ADR-0021 -- Comment-based docstrings for ASDL docs using YAML comments (block, inline, bundle). Tradeoff: requires comment-preserving parsing; structured doc fields are deferred.
- 2026-01-21: ADR-0022 -- Forbid spliced net names (LHS) in refactor pipeline; express segments as separate net entries. Canonical spec reconciliation deferred.
- 2026-01-19: ADR-0020 -- Tagged pattern axes for broadcast binding; axis_id derives from tag/name, match by subsequence with explicit errors; supersedes ADR-0019.
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
- 2026-01-06: The canonical pipeline is AST -> NFIR -> IFIR -> emit; prior CIR/NLIR staging is superseded and will be reconciled in `docs/specs/`. NLIR and CIR are merged into IFIR. (Superseded 2026-01-15)
- 2026-01-15: The canonical pipeline is AST -> GraphIR -> IFIR -> emit; NFIR is an optional authoring/roundtrip projection and is removed from the critical path. Rationale: keep GraphIR as the single semantic source of truth and prevent duplicated verification logic. Migration: move AST lowering directly into GraphIR builders, rebase IFIR lowering on GraphIR, and treat NFIR (if retained) as a derived view. Versioning: MVP-breaking change; no backward compatibility required.
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
