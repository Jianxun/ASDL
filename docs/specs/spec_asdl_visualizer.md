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
contain multiple module and device symbols. Symbols are expressed in grid
units; there is no per-symbol grid size (the schematic grid is a viewer
setting).

File naming:
- `path/to/design.asdl` -> `path/to/design.sym.yaml`

Schema (outline):
- `schema_version`: number (required, `0`)
- `modules`: mapping of `module_name` -> symbol definition
- `devices` (optional): mapping of `device_name` -> symbol definition

Module/device symbol definition (shared structure, adapted from
`prototype/symbol_renderer`):
- `body.w`, `body.h`: body size in grid units (required)
- `pins.top`, `pins.bottom`, `pins.left`, `pins.right`: arrays of pin entries:
  - `string`: pin name
  - `null`: spacing slot
  - `{pin_name: {offset?, visible?}}`: inline metadata for a pin entry
    - `offset`: optional fractional grid offset along the edge
    - `visible`: optional boolean (default `true`) to render the pin label
- `glyph` (optional, devices only for now):
  - `glyph.src`: path to SVG asset (relative to the `.asdl` file)
  - `glyph.viewbox`: optional SVG viewBox string (e.g., `"0 0 100 60"`)
  - `glyph.box`: placement box in grid units `{x, y, w, h}` (required when glyph is present)
Glyphs render inside `glyph.box` preserving aspect ratio; no implicit scaling
or placement is inferred beyond fitting within the box.

Pins are names only; direction is not tracked in the visualizer. Pin placement
is derived from `body` size and the pin arrays (see "Pin placement rules"). Pin
labels are optional per pin via `visible: false`.

Example (module + device):
```
schema_version: 0
modules:
  current_mirror_nmos:
    body: { w: 10, h: 6 }
    pins:
      left:
        - INP
        - INN: { offset: 0.25 }
        - null
        - BIAS
      right: [ OUT ]
      top: [ VDD ]
      bottom: [ VSS ]
devices:
  nfet_03v3:
    body: { w: 6, h: 4 }
    glyph:
      src: glyphs/nmos4.svg
      viewbox: "0 0 100 60"
      box: { x: 0.5, y: 0.5, w: 5, h: 3 }
    pins:
      left:
        - D
        - G: { visible: false }
      right: [ S, B ]
```

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
- `x`, `y`: grid coordinates in **grid units**.
  - Instances use **top-left** anchors (x,y are the top-left of the symbol body).
  - This avoids off-grid pins when `body.w/h` are odd.
- `orient`: Cadence-style orientation (`R0`, `R90`, `R180`, `R270`, `MX`, `MY`,
  `MXR90`, `MYR90`)
- `label`: optional display label

Net hub placement data:
- `groups`: array of hub placements in group order.
  - Net hub `x,y` are **center** coordinates in grid units.

Group order MUST align with `registries.schematic_hints.net_groups` emitted by
the compiler (derived from net endpoint list-of-lists). If the registry has no
groups, a single hub is assumed. User-defined extra hubs are not supported.

## Derived visualizer graph
The renderer builds an explicit node+edge graph:
- Nodes: instances, net hubs, optional port/junction helpers.
- Edges: one per endpoint, connecting instance pin handles to net hub handles.
- Handle IDs: pin names for instance/port pins; `hub` for net hubs.

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
6) **Labels**: pin and hub labels rotate with orientation but are never upside
   down; vertical text reads bottom-to-top. Pin labels render inside the body
   edge with a fixed inset.

## Interaction (MVP)
- Selecting an instance or hub exposes orientation controls:
  - **Rotate**: rotate 90° counter-clockwise.
  - **Mirror X**: mirror across the X axis (vertical flip).
  - **Mirror Y**: mirror across the Y axis (horizontal flip).
- Orientation edits update the in-memory layout `orient` field and are saved to
  `design.sch.yaml` when the user clicks **Save Layout**.

### Pin placement rules (symbols)
Pins are placed along the symbol body edges in grid units:
- Left/right arrays are ordered **top → bottom**
- Top/bottom arrays are ordered **left → right**
- `null` entries reserve a slot and advance spacing

Given:
- `N`: number of slots on that side (including `null`s)
- `step`: fixed at 1 grid unit
- `span = (N - 1) * step` (0 if `N == 1`)
- `edge_length`: `body.h` for left/right, `body.w` for top/bottom
- `start = floor((edge_length - span) / 2)` (bias toward origin; keeps pins on-grid)

For each slot index `i`:
- Left/right: `y = start + i * step + pin_offset`, `x = 0` (left) or `x = body.w`
- Top/bottom: `x = start + i * step + pin_offset`, `y = 0` (top) or `y = body.h`

`pin_offset` defaults to 0 and can be fractional grid units. The offset comes
from inline pin metadata when provided. It is the symbol author's
responsibility to align glyph artwork to the pin positions.

### Anchor rules (layout vs symbols)
- **Instances** are anchored by the **top-left** of the symbol body. Instance
  `x,y` in `design.sch.yaml` correspond to the top-left corner of the symbol
  bounding box in grid units.
- **Net hubs** remain **center-anchored**. Hub `x,y` represent the hub center in
  grid units (consistent with prior layouts).
- **Pin coordinates** are derived from the symbol body size and pin arrays, then
  offset from the instance top-left when rendering.
- The visualizer must convert between layout anchors and React Flow node
  top-left pixel coordinates as needed, but the persisted layout remains in
  grid units using the rules above.

### Orientation rules
Instances and net hubs use Cadence-style orientations with **R90 as
counter-clockwise rotation** in screen coordinates (x→right, y→down). Mirror
operations apply before rotation. The orientation enum set is exactly:
`R0`, `R90`, `R180`, `R270`, `MX`, `MY`, `MXR90`, `MYR90`.
- **MX** mirrors across the X axis (vertical flip): `y → h - y`.
- **MY** mirrors across the Y axis (horizontal flip): `x → w - x`.
- **Instances** rotate/mirror about the **top-left** origin of the symbol body.
- **Net hubs** rotate/mirror about the **center** of the hub.
- **Hub anchor**: a single hub handle starts on the **right** side for `R0` and
  is rotated/mirrored with the hub orientation.

Example (grid units):
- Symbol body `w=5`, `h=3` with pins on the left side: `[A, null, B]`
- Instance layout: `x=10`, `y=4` (top-left anchor)
- Left edge length = `h=3`, `N=3`, `span=(N-1)*1=2`, `start=floor((3-2)/2)=0`
- Pin slots (left side):
  - A at `(x=10, y=4 + 0 + 0)` → `(10, 4)`
  - B at `(x=10, y=4 + 2 + 0)` → `(10, 6)`
Both pins land on-grid even with an odd body size.

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
