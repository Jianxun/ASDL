# T-228: Visualizer Extension Refactor

## Goal
Split `extensions/asdl-visualizer/src/extension.ts` into focused modules under
`extensions/asdl-visualizer/src/extension/` while keeping behavior unchanged.

## Notes
- Keep `extension.ts` as a thin activate/deactivate entrypoint.
- Prefer small helper modules: commands, webview HTML loader, layout I/O,
  dump runner, symbols, paths/util, shared types.
- Ensure `npm run build` passes.
