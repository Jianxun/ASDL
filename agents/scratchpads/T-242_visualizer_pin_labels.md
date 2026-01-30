# T-242: Render numeric pin labels + forced labels in webview

## Scope
- Render numeric pattern labels at pin handles (`<3>`, `<3,1>`).
- Join multiple slices with `;` when forced by pin `label: always`.
- Labels must respect symbol orientation and sit inside the body edge.

## Files
- `extensions/asdl-visualizer/src/webview/app.tsx`
- `extensions/asdl-visualizer/src/webview/styles.css`
- `extensions/asdl-visualizer/src/webview/devHarness.ts`

## Verify
- `cd extensions/asdl-visualizer && npm run build`
