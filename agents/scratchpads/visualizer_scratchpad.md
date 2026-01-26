# Visualizer MVP (VSCode) — Implementation Plan

## Status
- Phase A not started.
- Next step: scaffold VSCode extension with WebView + load/save stub.
- Dependencies: none beyond repo; reuse React Flow prototype assets.

## Intent
We will not use the executor/reviewer workflow for this effort. The work is
interactive and UI-heavy, so decisions and iteration happen with the Architect
in the loop.

## MVP Goal (Ergonomics Validation)
Open a module in VSCode, view a schematic derived from PatternedGraph, drag
instances/net hubs, and save layout in-place as YAML sidecar.

## Phase A — VSCode WebView Loop (1–2 days)
- Add a minimal VSCode extension command: "ASDL: Open Visualizer".
- WebView loads a static mock graph (no ASDL integration yet).
- "Save Layout" triggers a write of `design.sch.yaml` next to the active
  `.asdl` (use a stub payload).
- Success: stable open/save loop in VSCode with in-place YAML write.

## Phase B — Real Data Hookup (2–4 days)
- Resolve `design.asdl` -> `design.sym.yaml` + `design.sch.yaml`.
- Accept a PatternedGraph JSON input path (manual selection or cached dump).
- Render instances + net hubs from the derived graph (adapter can be minimal).
- Success: visualizer opens on real designs with correct connectivity.

## Phase C — Editable Layout (3–5 days)
- Drag instances/hubs; update positions in memory.
- Save to `design.sch.yaml` with Cadence `orient` tokens preserved.
- Watch for file changes and hot-reload the view.
- Success: editing loop feels usable for real circuits.

## Phase D — Minimal Validation (2–3 days)
- Warn on layout entries that reference missing graph IDs.
- Validate hub group counts vs `schematic_hints.net_groups`.
- Provide “Reload from ASDL” button when mismatch.
- Success: clear non-blocking guardrails.

## Phase E — Symbol Integration (optional, after MVP)
- Parse `design.sym.yaml` for module symbols.
- Add device glyph mapping (simple built-in library).
- Success: symbols render with correct pins.

## Phase A — Implementation Plan (build-based, forward-compatible)
- Scaffold `extensions/asdl-visualizer/` with a VSCode extension entrypoint and a Vite + React webview app.
- Webview message contract:
  - `ready` (webview → extension)
  - `loadMock` (extension → webview) with mock graph + layout payload
  - `saveLayout` (webview → extension) with `{moduleId, layout}`
  - `diagnostics` (extension → webview) reserved for Phase D
- Webview renders a static mock graph from `loadMock`; button triggers `saveLayout`.
- Extension resolves active `.asdl` path and writes `design.sch.yaml` alongside it.
- Build outputs webview bundle to `extensions/asdl-visualizer/media/` and loads it with CSP-safe `webview.asWebviewUri`.
- Success: command opens webview, mock graph renders, and save writes YAML sidecar.

## Key Assumptions
- Single source of truth for connectivity is PatternedGraph.
- Sidecars are YAML and co-located with `.asdl` files.
- Graph sizes are small (tens of instances).

## Notes / Decisions
- Use VSCode WebView for in-place save and file watching.
- Hub grouping strictly follows `schematic_hints.net_groups`.
- Layout uses Cadence `orient`: R0/R90/R180/R270/MX/MY/MXR90/MYR90.
- Symbol definitions: unified module+device schema in `design.sym.yaml` (no pin direction),
  grid units only (no per-symbol grid size), optional SVG glyph for devices (relative to .asdl).
- Pin placement: side arrays ordered left/right top→bottom, top/bottom left→right; slot spacing fixed
  at 1 grid unit; `start = floor((edge_length - span)/2)`; optional per-pin fractional offsets.
- Layout coordinates stay center-based (grid units); React Flow uses top-left internally with conversion.
- Visualizer data: plan to add `asdlc visualizer-dump` CLI for minimal JSON per selected module,
  run via PATH, no dump files written to repo. Extension will prompt to select module when multiple.
- ADR candidate: visualizer schema + compiler integration decisions (symbol schema, pin placement rules,
  no per-symbol grid, CLI `visualizer-dump`, PATH resolution).
