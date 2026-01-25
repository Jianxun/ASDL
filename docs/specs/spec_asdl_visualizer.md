# ASDL Visualizer Spec (Prototype)

## Overview
This spec defines the prototype visualizer inputs and rendering rules.
Connectivity comes from the PatternedGraph JSON dump produced by the refactor
pipeline. Layout and symbol definitions live in YAML sidecars co-located with
the ASDL source files. The visualizer MUST NOT resolve or expand patterns on
its own; it renders pattern bundles as provided by the compiler.

## Goals
- Render patterned instances and nets without expanding patterns in the UI.
- Keep connectivity deterministic and sourced from PatternedGraph only.
- Allow user-edited, deterministic placement via schematic sidecars.
- Keep contracts minimal, stable, and easy to diff/version.

## Non-goals (for prototype)
- Inspection/troubleshooting panels.
- Smart layout optimization beyond basic grid snapping.
- Routing optimizations (no collision avoidance or bridge glyphs yet).
- Duplicate storage of connectivity inside layout sidecars.
- Browser-only persistence without an editor host.

## Inputs
### PatternedGraph JSON
Produced by `asdl patterned-graph-dump`. This is the single source of truth
for connectivity and pattern metadata. The visualizer reads:
- `modules`, `nets`, `instances`, `endpoints`
- `registries.pattern_expressions`, `pattern_origins`, `schematic_hints`

### Symbol sidecar (YAML, v0)
User-editable symbol definitions stored next to the ASDL file. One file may
contain multiple module symbols.

File naming:
- `path/to/design.asdl` -> `path/to/design.sym.yaml`

Schema (outline):
- `schema_version`: number (required, `0`)
- `modules`: mapping of `module_name` -> symbol definition
- `devices` (optional): mapping of `device_name` -> glyph mapping

Module symbol definition (reuses the YAML layout from `prototype/symbol_renderer`):
- `pins.top`, `pins.bottom`, `pins.left`, `pins.right`: arrays of pins
- Pins can be strings or `{name: {dir: in|out|inout}}`

Device glyph mapping example:
- `devices.nfet_03v3.glyph: nmos4`
- `devices.nfet_03v3.pin_map: { D: D, G: G, S: S, B: B }`

### Schematic sidecar (YAML, v0)
User-editable layout definitions stored next to the ASDL file. One file may
contain multiple module layouts. This file contains placement/orientation only;
it MUST NOT duplicate connectivity.

File naming:
- `path/to/design.asdl` -> `path/to/design.sch.yaml`

Schema (outline):
- `schema_version`: number (required, `0`)
- `modules`: mapping of `module_name` -> layout definition

Module layout definition:
- `grid_size`: number (optional, default 16)
- `instances`: mapping of `inst_id` -> placement data
- `net_hubs`: mapping of `net_id` -> hub placement data

Placement data:
- `x`, `y`: grid coordinates (center)
- `orient`: Cadence-style orientation (`R0`, `R90`, `R180`, `R270`, `MX`, `MY`,
  `MXR90`, `MYR90`)
- `label`: optional display label

Net hub placement data:
- `groups`: array of hub placements in group order

Group order MUST align with `registries.schematic_hints.net_groups` emitted by
the compiler (derived from net endpoint list-of-lists). If the registry has no
groups, a single hub is assumed. User-defined extra hubs are not supported.

## Derived visualizer graph
The renderer builds an explicit node+edge graph:
- Nodes: instances, net hubs, optional port/junction helpers.
- Edges: one per endpoint, connecting instance pin handles to net hub handles.
- Handle IDs: `<pin>@<atom>` for instance/port pins; `net@<atom>` for net hubs.

## Host integration (VSCode extension)
The primary UI host is a VSCode extension with a webview-based editor.

Responsibilities:
- Resolve companion files for an ASDL source:
  - `design.asdl` -> `design.sym.yaml` and `design.sch.yaml`
- Read and write YAML sidecars in-place via the VSCode file system API.
- Provide file watching or reload hooks when any of the inputs change.
- Expose a bridge API for the webview to request load/save and report diagnostics.

Fallbacks:
- Browser-only deployments may use download/upload or the File System Access API,
  but are not primary for this prototype.

## Prototype plan (phased)
Phase 0 - Feasibility spike:
- Open a webview, load a static sample graph, and write a dummy layout YAML file.
- Validate CSP, bundling, and in-place save via the VSCode file system API.

Phase 1 - Read-only viewer:
- Resolve `design.asdl` -> `design.sym.yaml` + `design.sch.yaml`.
- Load PatternedGraph JSON dump and render nodes/edges in the webview.

Phase 2 - Editable layout:
- Enable drag of instances/net hubs and save `design.sch.yaml` in-place.
- Watch for file changes and refresh the view.

Phase 3 - Minimal validation:
- Warn on layout entries that reference missing graph IDs.
- Validate hub group counts vs `schematic_hints.net_groups`.
- Surface diagnostics in a small panel or status bar.

## VSCode extension skeleton (outline)
Extension package layout:
- `extensions/asdl-visualizer/` (new)
- `extensions/asdl-visualizer/package.json`
- `extensions/asdl-visualizer/src/extension.ts`
- `extensions/asdl-visualizer/src/webview/index.tsx`
- `extensions/asdl-visualizer/src/webview/app.tsx`
- `extensions/asdl-visualizer/src/webview/styles.css`
- `extensions/asdl-visualizer/media/` (bundled web assets)

Core responsibilities:
- Register command `asdl.openVisualizer` to open the webview.
- Resolve companion files (`.sym.yaml`, `.sch.yaml`) from the active ASDL file.
- Read/write YAML files via `vscode.workspace.fs`.
- Bridge messages between webview and extension: `load`, `saveLayout`, `diagnostics`.

## Validation
- Layout entries MUST reference existing PatternedGraph IDs.
- Missing layout entries fall back to a default placement (diagnostic warning).
- Extra layout entries that do not match graph IDs are ignored with diagnostics.
- Net hub group counts MUST match `schematic_hints.net_groups` when present.
- Symbol pins MUST align with module/device port lists; mismatches emit diagnostics.
- When schematic data contradicts ASDL connectivity or structure, ASDL wins; the
  UI should surface a warning and allow the user to reload from ASDL.

## Rendering Rules
1) **Identity**: use explicit edges only; never connect by name or pattern.
2) **Crossings**: edge overlap is never connectivity. Only junction nodes connect.
3) **Junctions**: render as a small filled dot at the junction node.
4) **Grid**: positions are snapped to the module `grid_size`.
5) **Patterns**: render bundles as labels; do not expand patterns in the UI.

## Differential Nets
- A net with `atoms: ["P","N"]` is a diff net. Default render: a single bundled
  thick line between endpoints.
- At each endpoint, if the pin atom order differs from the net order, show a
  small swap glyph next to the pin label (e.g., `swap` icon).
- Optional debug view: render two thin lines (P and N) near the endpoint only.

Example binding (swapped polarity):
- Net: `stg1_out` atoms `["P","N"]`
- `MN_STG1.D` binds `["P","N"]` (no swap)
- `MN_STG2.G` binds `["N","P"]` (swap glyph)

## Notes
- This contract is intentionally small; extensions (layout hints, styling,
  troubleshooting panels) will be added later.
- Preferred host environment: VSCode extension with a webview-based editor to
  enable in-place save of YAML sidecars. Browser-only deployments may use
  download/upload fallbacks or the File System Access API, but are not primary.
- Expected graph sizes are small (tens of instances). Avoid premature
  performance optimizations in the MVP.
