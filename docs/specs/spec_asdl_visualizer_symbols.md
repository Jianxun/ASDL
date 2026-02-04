# ASDL Visualizer Symbols (Prototype)

## Symbol sidecar (YAML, v0)
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
    - `visible`: optional boolean (default `true`) to render the pin name label
    - `connect_by_label`: optional boolean (default `false`) to render the
      net/slice label at the pin (see routing spec)
  - Pin metadata entries MUST be single-key maps.
- `glyph` (optional, devices only for now):
  - `glyph.src`: path to SVG asset (relative to the `.asdl` file)
  - `glyph.viewbox`: optional SVG viewBox string (e.g., `"0 0 100 60"`)
  - `glyph.box`: placement box in grid units `{x, y, w, h}` (required when glyph is present)
Glyphs render inside `glyph.box` preserving aspect ratio; no implicit scaling
or placement is inferred beyond fitting within the box.

Pins are names only; direction is not tracked in the visualizer. Pin placement
is derived from `body` size and the pin arrays (see "Pin placement rules"). Pin
name labels are optional per pin via `visible: false`.

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

## Pin placement rules (symbols)
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
