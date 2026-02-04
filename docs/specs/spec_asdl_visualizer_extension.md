# ASDL Visualizer Extension (Prototype)

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
- Validate hub counts vs `schematic_hints.net_groups`.
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

## Interaction (MVP)
- Selecting an instance or hub exposes orientation controls:
  - **Rotate**: rotate 90° counter-clockwise.
  - **Mirror X**: mirror across the X axis (vertical flip).
  - **Mirror Y**: mirror across the Y axis (horizontal flip).
- Orientation edits update the in-memory layout `orient` field and are saved to
  `design.sch.yaml` when the user clicks **Save Layout**.
- The toolbar includes **Reload** to re-read `design.sym.yaml`/`design.sch.yaml`
  and refresh the graph without closing the view, preserving the current
  pan/zoom when possible.

## Validation
- Layout entries MUST reference existing PatternedGraph IDs.
- Missing layout entries fall back to a default placement (diagnostic warning).
- Extra layout entries that do not match graph IDs are ignored with diagnostics.
- Net hub counts MUST match `schematic_hints.net_groups` when present.
- Symbol pins MUST align with module/device port lists; mismatches emit diagnostics.
- When schematic data contradicts ASDL connectivity or structure, ASDL wins; the
  UI should surface a warning and allow the user to reload from ASDL.
