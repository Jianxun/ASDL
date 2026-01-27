# ADR-0029: Visualizer Symbol Schema, Glyph Placement, and Orientation/Label Rules

Status: Proposed

## Context
The visualizer symbol schema needs to carry more per-pin metadata (offsets,
label visibility) and explicit glyph placement. Orientation handling must be
consistent with Cadence-style enums, and labels should rotate without ever
rendering upside down. Existing `pin_offsets` and implicit glyph scaling are
too limiting for device symbols and add validation complexity.

## Decision
1) **Pin entries become inline metadata** in `design.sym.yaml`:
   - Pin arrays accept `string | null | {pin_name: {offset?, visible?}}`.
   - `offset` is a fractional grid delta along the edge.
   - `visible` defaults to `true`; `false` hides the pin label only.
   - `pin_offsets` is removed (no backward-compat for MVP).

2) **Explicit glyph placement**:
   - `glyph` includes `box: {x,y,w,h}` in grid units.
   - Glyph rendering preserves aspect ratio and fits within `glyph.box`.
   - No inferred placement or scaling beyond the box.

3) **Orientation and label rules**:
   - Use Cadence-style enums exactly: `R0`, `R90`, `R180`, `R270`, `MX`, `MY`,
     `MXR90`, `MYR90`.
   - R90 is counter-clockwise in screen coords (x→right, y→down).
   - Mirror applies before rotation; instances rotate about top-left origin,
     hubs about center.
   - Hub has a single handle that starts on the right for `R0` and is rotated
     with the hub.
   - Pin and hub labels rotate with orientation but are never upside down;
     vertical text reads bottom-to-top.

4) **Schema version stays at 0** for the prototype.

## Consequences
- Existing symbol sidecars using `pin_offsets` must be updated.
- Glyph authors must provide explicit placement boxes.
- Label rendering is deterministic and orientation-safe, but requires updated
  CSS and webview logic.

## Alternatives
- Keep `pin_offsets` and add parallel label metadata (rejected: split metadata).
- Auto-fit glyphs to the body bounds (rejected: ambiguous scaling/placement).
- Dynamic hub anchors based on edge geometry (rejected: prefer explicit orient).
