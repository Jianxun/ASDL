# T-241: Consume endpoint labels + pin label policy in extension graph

## Scope
- Add pin label policy to symbol schema: `label: auto|always|never`.
- Extend GraphPayload edges to carry `conn_label`.
- Prefer numeric `conn_label` over `label: always` for rendering decisions.

## Files
- `extensions/asdl-visualizer/src/extension/types.ts`
- `extensions/asdl-visualizer/src/extension/symbols.ts`
- `examples/pdks/gf180mcu/asdl/gf180mcu.sym.yaml`

## Verify
- `cd extensions/asdl-visualizer && npm run build`
