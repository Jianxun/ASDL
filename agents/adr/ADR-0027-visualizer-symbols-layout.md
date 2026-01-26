# ADR-0027: ASDL Visualizer Symbols, Pin Placement, and Layout Anchors

Status: Accepted

## Context
The ASDL Visualizer needs a stable symbol schema for modules and devices, a
pin placement algorithm that keeps pins on-grid, and a layout anchoring rule
that avoids off-grid pins when symbol sizes are odd. The visualizer should also
avoid writing compiler dumps to the repo and run the compiler implicitly.

Key constraints:
- Layout coordinates should remain grid-based and deterministic.
- Symbol definitions should be shared between module and device symbols.
- Pin direction is not part of ASDL and should not be modeled in the UI.
- Odd body sizes should not force off-grid pins.
- Visualizer data should be generated on-demand without writing files.

## Decision
1) **Unified symbol schema** in `design.sym.yaml` for modules and devices:
   - `body.w`, `body.h` in grid units.
   - `pins.top|bottom|left|right` arrays (names or `null` for spacing).
   - Optional `pin_offsets` per side, per pin (fractional grid units allowed).
   - Optional `glyph` for devices (`glyph.src` relative to `.asdl`, optional
     `glyph.viewbox`).
   - No pin direction fields.
   - No per-symbol grid size (viewer grid is global).

2) **Pin placement**:
   - Left/right arrays ordered top→bottom; top/bottom ordered left→right.
   - Slot spacing is 1 grid unit.
   - `start = floor((edge_length - span) / 2)` to keep pins on-grid with a
     consistent bias toward the origin.

3) **Layout anchors**:
   - Instance layout coordinates are **top-left** grid units.
   - Net hub coordinates remain **center** grid units.
   - This avoids off-grid pins for odd symbol body sizes while keeping hubs
     centered on the grid.

4) **Compiler integration**:
   - Add `asdlc visualizer-dump` to emit a minimal JSON payload for a selected
     module via stdout only.
   - The VS Code extension invokes `asdlc` from PATH and never writes dump files
     into the repo; it prompts for module selection when multiple modules exist.

## Consequences
- Existing center-based instance layout data must be migrated or reauthored.
- Visualizer adapter must convert between top-left instance placement and
  center-based net hubs.
- Symbol authors must align glyph artwork to pin positions.
- The extension depends on `asdlc` being available in PATH; missing compiler
  is a user-facing error.

## Alternatives
- Keep center-based instance placement and require even `body.w/h` sizes
  (rejected: burdens symbol authors and still allows off-grid pins if violated).
- Allow fractional instance coordinates (rejected: complicates snapping/editing).
- Permit per-symbol grid sizes (rejected: misalignment across symbols).
- Write PatternedGraph dumps to disk (rejected: repo pollution and larger data).
