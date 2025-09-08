# ASDL Import System – Import Phase Todos

## Current Status (Phase 1)
- Search-path policy implemented: `ASDL_PATH` only with fallback `["."]`; CLI/config paths ignored in resolver.
- Diagnostics split: E0441 strictly for "not found" (with probe candidates); E0446 implemented for load/parse failures.
- Basic DEBUG logs present; tracing helpers added (probe candidates, alias maps, collisions) — wiring expansion pending.
- `alias_resolution_map` created/used with absolute paths in validation/graph (path-identity cleanup partially complete).
- Flattening precedence flipped to local-wins with shadowing warning (conflict warned with E0601-style code).
- Single-source cycle detection: delegated to `FileLoader` (no duplicate check in orchestrator/graph).
- Determinism sorting intentionally skipped (per decision) for now.

## Decisions
- Keep imports under Elaborator `E` codes: reference errors `E04xx`, style/linting `E06xx`.
- Search paths: `ASDL_PATH` only; fallback `["."]`. CLI will not pass search paths; programmatic API retains `search_paths` param.
- Precedence: local modules must override imported on conflicts and emit a shadowing warning.
- Diagnostics: E0441 strictly for "not found" with explicit probe candidates; introduce E0446 for load/parse failures.
- Post-hoist metadata (Phase 3): drop `imports`/`model_alias` by default; optional debug retention.
- Relative paths: prepend the importing file's directory to the effective search roots per import, ahead of `ASDL_PATH` and fallback. Keep first-match-wins only when a single candidate exists.
- Ambiguity policy: if multiple candidate files match an import, emit a hard error (new `E0447` Ambiguous Import Resolution) listing candidates and how to disambiguate.

## Phase 1 – Remaining Work
- CLI: remove `--search-path` flag and plumbing (retain programmatic `search_paths`).
- Optional: re-enable unused warnings with `E0601`/`E0602` behind a flag.
- Implement importer-relative root: add `dir(importing_file)` to the front of effective roots during resolution.
- Implement ambiguity detection and `E0447` when >1 candidate file exists for an import.

## Phase 2 – Path Identity Cleanup (Backlog)
- Maintain `alias_resolution_map: file→{alias→resolved_abs_path}` and use it consistently end-to-end.
- Index `loaded_files` by resolved absolute paths only; remove raw-string keying.
- Consolidate or retire `ModuleResolver` path assumptions to avoid duplication.

## Phase 3 – Flattening Semantics (Backlog)
- After hoist/normalization, set `imports=None` and `model_alias=None` by default; add a debug-retain flag.
- Optional: pruning of unreachable modules (behind a flag).

## Phase 4 – Tracing/Docs/Tests (Backlog)
- Wire TRACE logs across graph/validator/flattener: effective paths, per-import probes, alias→path maps, cycle stacks, collisions.
- Tests: precedence; E0441 probe contents vs E0446 load errors; alias-usage tracking; path-identity resolution.
- Docs: update import orchestration, search path policy (ASDL_PATH-only), and troubleshooting; README added under `import_/`.

## Actionable Checklist
- [x] Replace default search roots to `["."]`; parse only `ASDL_PATH` in `PathResolver`.
- [ ] Remove CLI `--search-path` and related plumbing; keep programmatic `search_paths` API.
- [x] Flip flatten precedence to local-over-import; emit conflict warning.
- [x] Fix qualified alias usage tracking; optionally enable `E0601`/`E0602`.
- [x] Split diagnostics: strict E0441 with probe candidates; add E0446 for load/parse failures.
- [ ] Use `alias_resolution_map` with absolute paths end-to-end; stop indexing by raw strings.
- [ ] Drop `imports`/`model_alias` in flattened artifact; add debug-retain flag.
- [x] Add tracing helpers for paths, probe candidates, alias maps, cycles, collisions.
- [ ] Update docs and add focused tests.
- [ ] Prepend importing file directory to search roots (per import).
- [ ] Add `E0447` ambiguous import diagnostic and tests.
