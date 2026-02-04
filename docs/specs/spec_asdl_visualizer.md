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

## Notes
- This contract is intentionally small; extensions (layout hints, styling,
  troubleshooting panels) will be added later.
- Preferred host environment: VSCode extension with a webview-based editor to
  enable in-place save of YAML sidecars. Browser-only deployments may use
  download/upload fallbacks or the File System Access API, but are not primary.
- Expected graph sizes are small (tens of instances). Avoid premature
  performance optimizations in the MVP.
