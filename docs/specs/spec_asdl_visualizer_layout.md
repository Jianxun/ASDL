# ASDL Visualizer Layout (Prototype)

## Schematic sidecar (YAML, v0)
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
- `instances`: mapping of `inst_name` -> placement data
- `net_hubs`: mapping of `net_name` -> net hub entry (see below)

Placement data:
- `x`, `y`: grid coordinates in **grid units**.
  - Instances use **top-left** anchors (x,y are the top-left of the symbol body).
  - This avoids off-grid pins when `body.w/h` are odd.
- `orient`: Cadence-style orientation (`R0`, `R90`, `R180`, `R270`, `MX`, `MY`,
  `MXR90`, `MYR90`)
- `label`: optional display label

Net hub entry (v0):
- Preferred shape: `{ topology?, hubs }`
  - `topology`: `star | mst | trunk` (optional, default `star`)
  - `hubs`: mapping of `hub_name` -> placement
- Legacy shape (still accepted): `{ hub_name: placement }`
  - Interpreted as `{ topology: star, hubs: <legacy map> }`
If a net has no `net_hubs` entry, the visualizer uses default hub placement
and `star` topology for that net.

Net hub placement data:
- Hub placement mapping: `{ hub_name: placement }` (either the legacy map or
  the value of `hubs`).
  - Hub `x,y` are **center** coordinates in grid units.
  - `orient` rotates the hub’s launch direction for routed edges (see routing
    spec). Missing `orient` defaults to `R0`; missing hub placement uses the
    default layout placement rules.

Hub group order MUST align with `registries.schematic_hints.net_groups` emitted
by the compiler (derived from net endpoint list-of-lists). The hub group order
is the YAML map order of the hub placement mapping (`hubs` or the legacy map).
If the registry has no groups, a single hub group is assumed. User-defined
extra hubs are not supported.

Layout keys use instance/net display names. If names collide, the visualizer
uses `${name}#${id}` to disambiguate. Legacy layouts keyed by `inst_id` or
`net_id` are still accepted and will be migrated on save.

## Anchor rules (layout vs symbols)
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

## Orientation rules
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
