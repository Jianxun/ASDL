# Visualizer (React Flow) – MVP Plan

## Constraints (agreed)
- Ports: small filled circles are only for ASDL IO pins, not for transistor terminals
- Routing: use Manhattan (orthogonal) wiring
- Orientation: NMOS drain ↑, source ↓; PMOS drain ↓, source ↑

Reference: React Flow API v12 [reactflow.dev/api-reference](https://reactflow.dev/api-reference)

---
## Phase 0 – Scaffold & Base Canvas
- [X] Create `prototype/visualizer_react_flow/` with Vite (React + TS)
- [X] Add dependencies: `reactflow`, `zustand`, `tailwindcss` (or CSS Modules), `eslint`, `prettier`
- [X] Canvas: `<ReactFlow />` with `<Background />`, `<Controls />`, `<MiniMap />`
- [X] State: `useNodesState`/`useEdgesState`, `addEdge` on `onConnect`
- [X] Defaults: `defaultEdgeOptions={ type: 'step' }`, `connectionLineType='step'`, grid snap enabled

Acceptance:
- [ ] Pan/zoom/grid work; dummy nodes connect with orthogonal step edges

---
## Phase 1 – Node Types: Transistor and Port
- [X] `TransistorNode`: rectangle; terminals D/G/S positioned by flavor
  - NMOS: D=Top, S=Bottom, G=Left
  - PMOS: D=Bottom, S=Top, G=Left
  - Use `Handle` components for D/G/S but style handles invisible; render custom tick marks on edges so only IO ports show circles
- [X] `PortNode` (ASDL IO pin): small filled circle with a single `Handle`
  - Side: `left` or `right`; Direction: `in` | `out` | `bidir`

Acceptance:
- [ ] NMOS/PMOS anchors follow orientation; Port nodes render as solid dots; connections possible

---
## Phase 2 – Manhattan Routing & Connection Rules
- [X] Use built‑in `step` edges for orthogonal routing (`defaultEdgeOptions` + `connectionLineType`)
- [X] Enable `snapToGrid` with tuned `snapGrid`
- [X] `isValidConnection` allowing same‑node different‑handle connections; still blocks identical handle loops; allow multi‑edges per terminal

Acceptance:
- [ ] All connections appear orthogonal; invalid connects rejected

---
## Phase 3 – Toolbar & Inspector
- [ ] Toolbar: add NMOS, PMOS, Port(L), Port(R); zoom fit; delete selected
- [ ] Inspector: edit selected node props (name, flavor, W/L; port label/side)
- [ ] State: Zustand for UI; sync to React Flow via `setNodes`/`updateNodeInternals`

Acceptance:
- [ ] Add/edit/delete elements; visual updates are immediate

---
## Phase 4 – Custom Manhattan Edge (optional)
- [ ] Implement `ManhattanEdge` using `BaseEdge` to improve elbow placement
- [ ] Simple router: horizontal‑first/vertical‑first with optional rounded corners

Acceptance:
- [ ] Edge detours look cleaner than default `step` in common cases

---
## Phase 5 – Persistence & Session Restore
- [ ] Export/import `{ nodes, edges }` JSON (use `useReactFlow().toObject()` when suitable)
- [ ] Autosave to `localStorage`; `fitView` after import

Acceptance:
- [ ] Reload restores prior graph; manual round‑trip works

---
## Phase 6 – Quality & Polish
- [ ] Undo/redo, copy/duplicate, multi‑select
- [ ] Helper lines/snaplines; dark mode theme
- [ ] Tooltips on handles; net highlight on hover
- [ ] Minimal tests (Vitest + RTL) for node/edge behaviors

---
## Notes
- Only `PortNode` uses small filled circles; transistor terminals have invisible handles with visible tick marks
- Start with gate on left for both NMOS/PMOS; revisit later if needed
- Ignore legacy jsPlumb prototype; this is a clean slate