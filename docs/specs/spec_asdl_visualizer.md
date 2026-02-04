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

## Spec map
- Symbols: `docs/specs/spec_asdl_visualizer_symbols.md`
  - `.sym.yaml` schema, pin metadata, glyphs, pin placement rules.
- Layout: `docs/specs/spec_asdl_visualizer_layout.md`
  - `.sch.yaml` schema, placement/orientation rules, hub grouping.
- Routing: `docs/specs/spec_asdl_visualizer_routing.md`
  - Derived graph, star/mst/trunk routing, labels, rendering rules.
- Extension/host integration: `docs/specs/spec_asdl_visualizer_extension.md`
  - VSCode integration, commands, interaction, validation.

## Inputs (summary)
- PatternedGraph JSON dump from `asdl patterned-graph-dump` (details in routing spec).
- Symbol sidecar `.sym.yaml` (details in symbols spec).
- Schematic sidecar `.sch.yaml` (details in layout spec).

## Proposal: symbol sidecar generation + editing
### Editor choice
Reuse the existing schematic visualizer webview with a **symbol editor mode**
(single-node canvas) rather than a dedicated editor. This keeps the renderer,
grid math, pin placement rules, and orientation logic unified, and minimizes
new UI surface area. The mode swaps the graph view for a single symbol canvas
and emits `.sym.yaml` edits instead of layout edits.

### Generation workflow (stub `.sym.yaml`)
Add a CLI helper to generate or refresh symbol sidecars from an ASDL file:
- **Command (proposed):** `asdl visualizer-symbols` (name TBD).
- **Output:** `design.sym.yaml` with `schema_version: 0`, plus `modules` and
  `devices` entries populated from the entry file (and imported device defs as
  needed).
- **Defaults:** `body.w/h` chosen from pin count (simple heuristic), and pins
  assigned to left/right by default (or all on left for 1-sided symbols).
- **Merge option:** `--merge` adds missing symbols/pins without overwriting
  existing entries (used by the editor’s “Reset from ASDL” action).

### Minimal UI/actions (symbol editor mode)
- **Select symbol:** pick module/device from a dropdown (from ASDL/sidecar).
- **Body size:** drag handles or numeric inputs for `body.w/h` (grid units).
- **Pins list:** edit per-side pin arrays with drag-to-reorder, add/remove
  `null` slots, and inline metadata toggles (`visible`, `offset`,
  `connect_by_label`).
- **Pin alignment helpers:** snap pins to grid; show slot index and computed
  position based on the placement rules in `spec_asdl_visualizer_symbols.md`.
- **Glyph placement (devices):** choose an SVG asset path, optional viewBox,
  and drag/resize the `glyph.box` overlay on the symbol body.
- **Save / Reload:** persist to `.sym.yaml`, or reload from disk without closing
  the editor.

### Glyph positioning rules (editor behavior)
- All symbol geometry is in **grid units**, anchored at the symbol body’s
  **top-left** origin `(0,0)`.
- `glyph.box` is stored as `{x, y, w, h}` in grid units relative to the body.
  The editor uses grid snapping (integer units) and preserves aspect ratio
  when resizing unless a modifier key is held.
- Pin positions are derived from `body.w/h` and pin arrays; the editor does not
  auto-align glyph art beyond showing its current box vs. computed pin slots.

### Schema changes / new commands
- **Schema:** no changes required for v0; the existing `.sym.yaml` schema is
  sufficient for an MVP editor. Optional future extension: allow `glyph` for
  modules or multiple glyphs for richer symbols.
- **Commands:** add a CLI helper (`asdl visualizer-symbols`, name TBD) to
  generate/merge symbol sidecars; no changes to the patterned-graph dump.

## Notes
- This contract is intentionally small; extensions (layout hints, styling,
  troubleshooting panels) will be added later.
- Preferred host environment: VSCode extension with a webview-based editor to
  enable in-place save of YAML sidecars. Browser-only deployments may use
  download/upload fallbacks or the File System Access API, but are not primary.
- Expected graph sizes are small (tens of instances). Avoid premature
  performance optimizations in the MVP.
