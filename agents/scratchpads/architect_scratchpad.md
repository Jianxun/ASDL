# Architect Scratchpad

## Architecture notes (session summary; not yet ADRs)
## Current status (2026-02-24)
- Executor delivery wave completed:
  - `T-303` done, merged via PR #326.
  - `T-304` done, merged via PR #327.
- Latest merged changes are pulled locally; task state now reflects both as
  `done`.
- Reachable-only emission cutover is in place with ADR-0036 policy:
  - emission rooted at final resolved top
  - emit reachable modules only
  - keep default naming as `cell`, non-default as `cell_<view>`
- Next architecture focus moved to query tooling:
  - new spec drafted: `docs/specs/spec_cli_query.md`
  - command group: `asdlc query`
  - planned subcommands: `tree`, `bindings`, `emit-plan`, `refs`,
    `instance`, `net`, `net-trace`
  - traversal order semantics documented (`dfs-pre`, `dfs-post`)
  - v0.x open decisions captured for pre-implementation closure

## Current status (2026-02-23)
- Finalized view/emission collision strategy and logging consolidation decisions.
- Specs updated:
  - `docs/specs/spec_asdl_views.md`
  - `docs/specs/spec_asdl_view_config.md`
  - `docs/specs/spec_netlist_emission.md`
  - `docs/specs/spec_cli.md`
- ADRs added:
  - ADR-0034: DFS-stable ordinal collision naming (`base`, `base__2`, ...)
  - ADR-0035: consolidated compile log via `--log` with default
    `<entry_file_basename>.log.json`
- Policy decisions locked:
  - Keep `cell@default` normalization to default realization.
  - Hard cutover from `--binding-sidecar` to compile log artifact.
  - Deprecate/remove `__occ_*` occurrence-specialized naming for consistency
    with global collision allocator.
  - Emit warnings for missing/unknown `file_id` (non-fatal).
- Task housekeeping completed:
  - Archived done tasks: `T-297`, `T-298`.
  - Active sprint sliced to: `T-299`..`T-302`.
  - State file lint passes after updates.

## Execution packet (2026-02-23)
- Recommended implementation order:
  1. `T-299` collision allocator + warning + mapping data
  2. `T-300` remove `__occ_*` path / align apply behavior
  3. `T-301` CLI `--log` + compile log schema + hard cutover
  4. `T-302` provenance-warning and deterministic regression hardening
- Required acceptance themes:
  - deterministic emission naming under collisions
  - deterministic compile-log content/order
  - stable warning behavior for provenance gaps
  - removal of hash-name and sidecar-only legacy assertions

## Deferred follow-up (2026-02-22)
- Deferred CLI hierarchy introspection (`asdlc hier`) to a later cycle.
- Resume with subcommands oriented for agent/tooling use:
  - `asdlc hier modules <entry.asdl>`
  - `asdlc hier tree <entry.asdl> --top <module> [--depth N] [--json]`
  - `asdlc hier refs <entry.asdl> --module <module> [--ref <regex>] [--json]`
  - `asdlc hier paths <entry.asdl> --from <inst_path> --to <inst_path>`
- Keep initial scope read-only and PatternedGraph-based (no query DSL in v1).
## Current status (2026-01-28)
- Visualizer dev loop added on branch `feature/webview-harness`: webview dev harness,
  Playwright viewport test, and payload builder script for real .asdl fixtures.
- Fixed VS Code webview flicker/reset by removing runtime mutation of
  `webview.options` during glyph resolution.
- Added discrete orient transforms (R0/R90/R180/R270/MX/MY/MXR90/MYR90) in the
  webview; glyphs rotate/mirror with symbols and handle routing updates with
  oriented pin positions.
- Updated gf180mcu nmos/pmos glyph strokes to white for visibility.
  Recent commits: b36211f, 9ff80cf, 1218750 on `feature/webview-harness`.
## Current status (2026-01-30)
- PR #251 merged to `main` with visualizer layout/hub schema changes, name-keyed
  layouts, hub orient handling, grid-aligned edges/handles, and scratchpads for
  T-240/T-241/T-242.
- Visualizer spec updated to document numeric pattern pin labels (`<3>`, `<3,1>`)
  and `;`-joined slices. Default hub launch direction is right-facing.
- User requested redefining pin labeling: replace `label` policy with
  `connect_by_label` to mean “show net label outside the symbol near the pin
  handle and suppress the wire; pin name labels remain inside.”
- User stated T-240/T-242 are done; next session should update tasks state/archive
  accordingly and rename schema fields to `connect_by_label`.
## Current status (2026-01-24)
- Implemented stricter AtomizedGraph validation and binding rules; diagnostics now flag
  duplicate instance names, duplicate instance ports, and nets with zero endpoints.
- Port order atomization now stays literal-only and requires registry-backed expansion
  for patterns; non-literal fallback is disallowed.
- Tests updated to cover port order expansion and endpoint uniqueness.
- Work is committed on feature branch `feature/atomized-graph-strictness` (commit 537ab06).
- Next session: refactor `src/asdl/lowering/patterned_graph_to_atomized.py` into modular
  chunks while preserving current behavior and diagnostics.

GraphIR core:
- Move GraphIR to dataclass-based core model; pydantic stays on AST only.
- Drop xDSL textual IR and pass pipeline; replace with a simple, custom pass runner.
- GraphIR entities stay "boring": stable IDs + structure only; no provenance on ops.

Metadata system (external registries):
- Provenance/annotations live in registries keyed by GraphId.
- Pattern metadata stored as:
  - PatternExpressionRegistry: expr_id -> parsed pattern expression.
  - PatternOriginIndex: entity_id -> (expr_id, segment_index, atom_index).
  - ParamPatternOriginIndex: (inst_id, param_name) -> (expr_id, atom_index).
  - SourceSpanIndex: entity_id -> source span.
- Avoid per-atom storage of base_name/pattern_parts on graph nodes.

Lowering and pattern modularity:
- AST->GraphIR should be a staged pipeline: resolve symbols -> parse pattern table ->
  build GraphSeed (pattern refs, no expansion) -> bind/expand plan -> materialize GraphIR.
- Pattern logic lives in a dedicated pattern service (parse/validate/bind/expand),
  with stateless verifiers and clear inputs/outputs.

API vs CLI boundaries:
- CLI is a thin wrapper over a programmatic API.
- API should expose: parse/load, build_graph, verify, pattern tooling,
  design queries, and emission (no CLI-only globals).
- Diagnostics are always returned as data, not raised.

Schematic / visualization:
- Schematic should consume non-atomized views (PatternedGraph/GraphSeed or
  coalesced view derived from registries).
- Schematic will not support zoomable expansion for now.

Endpoints list-of-lists (authoring + schematic hints):
- Allow `endpoints` as list-of-lists for authoring convenience and visualization hints.
- Semantics unchanged: flatten deterministically for GraphIR (outer order, then inner).
- Record group boundaries in a schematic hints registry keyed by net_id.
- UI renders groups as net nodes, star-connected via the first group as hub.

Named pattern axes / broadcast (in new architecture):
- Axis metadata and binding rules live in the pattern service + registries only.
- GraphIR/PatternedGraph nodes carry only expr_id references, no axis info.
- Named-axis broadcast matches by axis_id; shared axes must match sizes, missing
  axes broadcast (subsequence rule for axis order).

PatternedGraph structure (no atomized nodes):
- NetBundle: net_id, name_expr_id, endpoint_ids.
- EndpointBundle: endpoint_id, net_id, port_expr_id (no inst_id; may expand to
  multiple instances).
- InstanceBundle: inst_id, name_expr_id, ref_sym, param_expr_ids.
- Pattern registry stores segments/axes; binding plans map net expr to endpoint expr.
