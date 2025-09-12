## Visualizer (React Flow)

Interactive schematic viewer for ASDL modules using React Flow v12. The CLI exports a graph JSON; the app renders primitive symbols (NMOS, PMOS, resistor, capacitor) by exact model match or a generic block for other instances.

### Export and serve
- Export: `asdl visualize <file.asdl> [--module <name>] [--no-serve] [--inline/--no-inline]`
- Output: `{basename}.{module}.sch.json` next to the ASDL file
- Serve: by default the CLI launches Vite at `http://localhost:5173`
- Inline mode: JSON passed via `?data=`; otherwise copied to `public/graph.json`
- Env overrides: `ASDL_VIS_VITE_DIR`, `ASDL_VIS_PUBLIC_DIR`

### JSON schema (v2)
Two node kinds:
- Port node (legacy-compatible):
```json
{
  "id": "vin",
  "type": "port",
  "data": { "name": "vin", "side": "left", "direction": "in" },
  "position": { "gx": 6, "gy": 6 }
}
```
- Instance node (generic for all instances):
```json
{
  "id": "mn1",
  "type": "instance",
  "model": "nmos",
  "pin_list": { "D": {}, "G": {}, "S": {} },
  "position": { "gx": 20, "gy": 6 }
}
```
Notes:
- `pin_list` keys are pin names; optional per-pin metadata: `role`, `type`, `dir`.
- Edges use handle ids matching pins: ports use `P`; instances use each pin key.

### Primitive symbols (exact model match)
- `nmos` → NMOS symbol
- `pmos` → PMOS symbol
- `res` → Resistor symbol (handles: PLUS top, MINUS bottom)
- `cap` → Capacitor symbol (handles: PLUS top, MINUS bottom)
Any other `model` renders as a generic block with per-pin handles.

### Layout and persistence
- Grid-based coordinates in `position.gx/gy` represent node centers
- Auto-placement provides initial layout; drag to arrange
- Save Layout downloads JSON with updated positions; replace the exported file to persist positions across runs

### Development
- Start app: `npm install && npm run dev`
- Typical flow: run CLI export → adjust layout in browser → Save Layout
