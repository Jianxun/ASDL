# ASDL Import System – Import Phase Todos

## Current Status
- Phase 1.2 MVP complete; enhancements through 1.2.6 shipped (2025-08-25)
- Core components integrated; CLI supports `--search-path`; diagnostics E0441–E0445 active
- Quality warnings added: I0601 (unused import), I0602 (unused model_alias)

## Recent Enhancements
- E0443/E0444 post-load validation of qualified instance references
- E0441 includes explicit probe paths
- CLI netlist gated: generation skipped when ERROR diagnostics exist
- Unit tests updated; CLI toy integration test scaffolded

## Remaining Work
- Config file support for search paths (asdl.config.yaml)
- Additional integration tests (toy variants, transitive scenarios)
- Prune unreachable modules based on top/--top; deterministic module order
- Documentation: user guide, import tutorial, ASDL_PATH best practices

## Tracing & Logging (Next Session)
- [ ] Structured tracing for import resolution
  - [ ] Log search paths (ASDL_PATH, CLI --search-path) and probe order
  - [ ] Log per-import alias resolution → absolute path mapping
  - [ ] Log circular detection stack transitions
- [ ] Model resolution trace
  - [ ] Show how qualified refs `alias.module` are stripped and mapped via `model_alias`
  - [ ] Emit a per-file alias table in verbose mode
- [ ] CLI verbosity
  - [ ] `--verbose` shows tracing; `--trace-imports` for focused import logs
  - [ ] Optional `--trace-id` to group logs per run
- [ ] Tests
  - [ ] Unit: path resolver probe lists
  - [ ] Integration: trace output contains expected lines for toy example

## Tests
- Unit: E0443/E0444 reference validation
- Unit: E0441 probe paths in missing import diagnostics
- Unit: Alias resolver validations and collisions
- Integration: CLI toy netlist (complete and extend)

## Notes
- Simplicity-first: direct file path imports; ASDL_PATH resolution
- Model names normalized during flattening; aliases applied pre-elaboration

---

## Analysis: Current Issues and Decisions

### Identified brittleness/gaps
- Module precedence mismatch: docs expect local modules to override imported; current code lets imported override local in flattening.
- Flattening semantics: imports/model_alias should be dropped post-hoist; optional prune of unreachable modules; not implemented.
- Path identity inconsistency: `loaded_files` keyed by absolute paths while validation uses raw `Path(import_str)`; requires a consistent alias→resolved-path map.
- Qualified ref usage tracking bug: per-instance tracking uses a `for … else` in the wrong scope; unused-alias linting is suppressed.
- Diagnostics conflation: E0441 used for both not-found and load/parse failures; probe list should show explicit candidates.
- Duplicate circular checks: both orchestrator and loader detect cycles; keep one source of truth.
- Determinism: module hoist/merge order is not explicitly stabilized.
- Tracing/logging: insufficient visibility into search paths, probe order, alias→path mapping, cycle stacks.

### Decisions (preliminary)
- Search paths policy: use `ASDL_PATH` only; fallback is `["."]`. Remove CLI `--search-path` to simplify mental model.
- Resolution location: elaborator resolves `ASDL_PATH` internally (via `PathResolver`). Keep API param `search_paths` for programmatic callers/tests; CLI will not pass paths.
- Precedence: local modules override imported on name collisions; emit a warning when shadowing occurs.
- Determinism: stabilize output by sorting module names and applying a stable import traversal when hoisting.
- Diagnostics: split not-found vs load/parse failure; E0441 for not-found with explicit probe list; add new code (e.g., E0446) for load/parse errors.
- Metadata post-hoist: drop `imports` and `model_alias` in flattened output by default; consider a debug flag to retain for inspection.

---

## Preliminary Refactor Plan (Phased)

### Phase 1 – Behavior and diagnostics (low risk)
- Change flatten precedence to prefer local modules; warn on conflicts.
- Stabilize module order (sorted names) and imported traversal.
- Fix qualified model-alias usage tracking bug; optionally re-enable unused import/alias warnings (I0601/I0602).
- Split diagnostics: keep E0441 strictly for "file not found" with explicit probe candidates; introduce E0446 for load/parse failures.
- Single cycle detection: rely on `FileLoader` to emit E0442; remove duplicate detection in orchestrator.

### Phase 2 – Path identity and binding cleanup
- Maintain `alias_resolution_map: file→{alias→resolved_abs_path}` and use it consistently.
- Update validation/binding to index `loaded_files` by resolved absolute paths only.
- Either wire `ModuleResolver` into orchestrator validation/binding or fold its logic to avoid duplication.

### Phase 3 – Flattening semantics and options
- After hoist/normalization, set `imports=None` and `model_alias=None` in the flattened `ASDLFile` by default.
- Optional: implement pruning of unreachable modules based on selected top; provide a flag to disable for debug.

### Phase 4 – Tracing/logging and docs/tests
- Add DEBUG/TRACE logs: effective search paths, per-import probe lists, alias→path mapping, cycle stacks, and precedence decisions on collisions.
- Tests: precedence, determinism, E0441 probe contents vs E0446 load errors, alias usage tracking, path identity resolution.
- Docs: update import orchestration, search path policy (ASDL_PATH-only, fallback `.`), and troubleshooting.

---

## Search Path Policy (to implement)
- Effective search roots: `ASDL_PATH` (colon-separated) → fallback `["."]` when unset.
- No config file dependency; introduce later without breaking this model.
- CLI: remove `--search-path`; document `ASDL_PATH` usage (e.g., `examples/setup.sh` already exports it).
- Diagnostics: E0441 must list the exact probe candidates from the effective roots.

---

## Action Items (executable tasks)
- [ ] Replace default search roots to `["."]`; parse only `ASDL_PATH` in `PathResolver`.
- [ ] Remove CLI `--search-path` and related plumbing; keep programmatic `search_paths` API.
- [ ] Flip flatten precedence to local-over-import; emit conflict warning.
- [ ] Stabilize hoist/merge order; add unit tests for determinism.
- [ ] Fix qualified alias usage tracking; consider enabling I0601/I0602.
- [ ] Split diagnostics: strict E0441 with probe list; new E0446 for load/parse failures.
- [ ] Use `alias_resolution_map` with absolute paths end-to-end; stop indexing by raw strings.
- [ ] Drop `imports`/`model_alias` in flattened artifact; add flag to retain for debug.
- [ ] Add tracing logs for paths, probes, alias maps, cycles, and collisions.
- [ ] Update docs (orchestration + dependency management) and add focused tests.