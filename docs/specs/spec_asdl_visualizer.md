# ASDL Visualizer Spec (Prototype)

## Overview
This spec defines the prototype visualizer input contract and rendering rules.
The visualizer consumes a topology dump produced by the ASDL compiler pipeline.
Edge connectivity is fully prepared by compiler passes (atomized patterns).
The visualizer MUST NOT resolve or expand patterns on its own.

Source of truth is IFIR after PatternAtomizePass (ADR-0011), exported as JSON.

## Goals
- Render instance groups unexpanded while wiring atomized endpoints.
- Avoid ambiguous wiring; overlays never imply connectivity.
- Support differential nets with clear swap indication.
- Keep the JSON contract minimal and deterministic.

## Non-goals (for prototype)
- Inspection/troubleshooting panels.
- Layout optimization or auto-placement beyond basic grid snapping.
- Routing optimizations (no collision avoidance or bridge glyphs yet).

## JSON Contract (v0)
Top-level:
- `schema_version`: number (required, `0` for this prototype)
- `grid_size`: number (optional, default 16)
- `nodes`: array of Node
- `edges`: array of Edge

Node:
- `id`: string (unique)
- `type`: `instance` | `port` | `net` | `junction`
- `position`: `{ gx: number, gy: number }` (center in grid units)
- `data`: object (type-specific)

Instance node data:
- `label`: string (e.g., `MN_STG1<P|N>`)
- `pattern_origin`: string (same grouping key as compiler output)
- `atoms`: ordered array of atom labels (e.g., `["P","N"]`)
- `pins`: array of Pin

Pin:
- `id`: string (e.g., `D`, `G`, `S`)
- `label`: string (display label)
- `atoms`: ordered array (pin atom order; may differ from net atom order)
- `bind_label`: string (optional, e.g., `stg1_out<P|N>` for display only)

Port node data:
- `label`: string (e.g., `$OUT`)
- `atoms`: ordered array (optional for diff ports)

Net node data:
- `label`: string (e.g., `stg1_out<P|N>`)
- `atoms`: ordered array (optional; if length 2 and tokens are `P`/`N`, render as diff)
- `display`: `{ kind: "diff" | "scalar", bundle: "thick" | "thin" }` (optional)

Junction node data:
- `label`: string (optional)

Edge:
- `id`: string
- `source`: string (node id)
- `source_handle`: string (handle id)
- `target`: string (node id)
- `target_handle`: string (handle id)
- `display`: `{ attach: "handle" | "label" }` (optional; label attachment is visual only)

Handle IDs:
- Instance/port pins expose one handle per atom: `<pin>@<atom>` (e.g., `D@P`)
- Net nodes expose one handle per atom: `net@<atom>` (e.g., `net@N`)
- Junction nodes expose a single handle: `j`

## Rendering Rules
1) **Identity**: use explicit edges only; never connect by name or pattern.
2) **Crossings**: edge overlap is never connectivity. Only junction nodes connect.
3) **Junctions**: render as a small filled dot at the junction node.
4) **Labels**: pin `bind_label` is display-only and must not change connectivity.
5) **Grid**: positions are snapped to `grid_size`.

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
