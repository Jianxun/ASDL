import React, { useCallback, useEffect, useMemo, useState } from 'react'
import ReactFlow, {
  Background,
  ConnectionLineType,
  Controls,
  Position,
  Handle,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeProps,
  type NodeTypes
} from 'reactflow'
import 'reactflow/dist/style.css'

declare function acquireVsCodeApi(): { postMessage: (message: unknown) => void }

type InstanceNode = {
  id: string
  label: string
  pins: string[]
  symbolKey: string
}

type NetHubNode = {
  id: string
  label: string
}

type GraphPayload = {
  moduleId: string
  instances: InstanceNode[]
  netHubs: NetHubNode[]
  edges: Array<{ id: string; from: string; to: string }>
  symbols: Record<string, SymbolDefinition>
}

type SymbolPins = {
  top?: Array<SymbolPin | null>
  bottom?: Array<SymbolPin | null>
  left?: Array<SymbolPin | null>
  right?: Array<SymbolPin | null>
}

type SymbolPin = {
  name: string
  offset: number
  visible: boolean
}

type SymbolGlyph = {
  src: string
  viewbox?: string
  box: { x: number; y: number; w: number; h: number }
}

type SymbolDefinition = {
  body: { w: number; h: number }
  pins: SymbolPins
  glyph?: SymbolGlyph
}

type Orientation = 'R0' | 'R90' | 'R180' | 'R270' | 'MX' | 'MY' | 'MXR90' | 'MYR90'

type OrientationSpec = {
  key: Orientation
  mirrorX: boolean
  mirrorY: boolean
  rotation: 0 | 90 | 180 | 270
}

type GlyphRender = {
  src: string
  viewbox?: string
  box: { x: number; y: number; w: number; h: number }
}

type Placement = {
  x: number
  y: number
  orient?: string
  label?: string
}

type LayoutPayload = {
  schema_version: number
  modules: Record<
    string,
    {
      grid_size?: number
      instances: Record<string, Placement>
      net_hubs: Record<string, { groups: Placement[] }>
    }
  >
}

type LoadGraphMessage = {
  type: 'loadGraph'
  payload: {
    graph: GraphPayload
    layout: LayoutPayload
    diagnostics?: string[]
  }
}

type DiagnosticsMessage = {
  type: 'diagnostics'
  payload: { items: string[] }
}

type WebviewMessage = LoadGraphMessage | DiagnosticsMessage

const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi() : null
const DEFAULT_GRID_SIZE = 16
const HUB_SIZE = 2
const HUB_HANDLE_ID = 'hub'
const FALLBACK_SYMBOL: SymbolDefinition = {
  body: { w: 6, h: 4 },
  pins: { left: [] }
}
const ORIENT_SPECS: Record<Orientation, OrientationSpec> = {
  R0: { key: 'R0', mirrorX: false, mirrorY: false, rotation: 0 },
  R90: { key: 'R90', mirrorX: false, mirrorY: false, rotation: 90 },
  R180: { key: 'R180', mirrorX: false, mirrorY: false, rotation: 180 },
  R270: { key: 'R270', mirrorX: false, mirrorY: false, rotation: 270 },
  MX: { key: 'MX', mirrorX: true, mirrorY: false, rotation: 0 },
  MY: { key: 'MY', mirrorX: false, mirrorY: true, rotation: 0 },
  MXR90: { key: 'MXR90', mirrorX: true, mirrorY: false, rotation: 90 },
  MYR90: { key: 'MYR90', mirrorX: false, mirrorY: true, rotation: 90 }
}

type InstanceNodeData = {
  label: string
  orient: string
  body: { w: number; h: number }
  pins: PinPosition[]
  gridSize: number
  glyph?: GlyphRender
}

type HubNodeData = {
  label: string
  orient: string
  gridSize: number
}

type VisualNodeData = InstanceNodeData | HubNodeData

type PinSide = 'top' | 'bottom' | 'left' | 'right'

type PinPosition = {
  id: string
  name: string
  side: PinSide
  x: number
  y: number
  visible: boolean
}

export function App() {
  const [graph, setGraph] = useState<GraphPayload | null>(null)
  const [layout, setLayout] = useState<LayoutPayload | null>(null)
  const [diagnostics, setDiagnostics] = useState<string[]>([])
  const [gridSize, setGridSize] = useState<number>(DEFAULT_GRID_SIZE)
  const [nodes, setNodes, onNodesChange] = useNodesState<VisualNodeData>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  const nodeTypes = useMemo<NodeTypes>(() => ({
    instance: InstanceNodeComponent,
    hub: HubNodeComponent
  }), [])

  useEffect(() => {
    const handleMessage = (event: MessageEvent<WebviewMessage>) => {
      const message = event.data
      if (message.type === 'loadGraph') {
        setGraph(message.payload.graph)
        setLayout(message.payload.layout)
        if (message.payload.diagnostics) {
          setDiagnostics(message.payload.diagnostics)
        }
        const moduleLayout = message.payload.layout.modules[message.payload.graph.moduleId]
        const grid = moduleLayout?.grid_size ?? DEFAULT_GRID_SIZE
        setGridSize(grid)
        const { nodes: rfNodes, edges: rfEdges } = buildReactFlowGraph(
          message.payload.graph,
          moduleLayout,
          grid
        )
        setNodes(rfNodes)
        setEdges(rfEdges)
      }
      if (message.type === 'diagnostics') {
        setDiagnostics(message.payload.items)
      }
    }

    window.addEventListener('message', handleMessage)
    vscode?.postMessage({ type: 'ready' })

    return () => {
      window.removeEventListener('message', handleMessage)
    }
  }, [])

  const onSave = useCallback(() => {
    if (!layout || !graph) {
      return
    }
    const moduleId = graph.moduleId
    const nextLayout: LayoutPayload = {
      schema_version: layout.schema_version ?? 0,
      modules: { ...layout.modules }
    }
    const existingModule = nextLayout.modules[moduleId]
    const moduleLayout = {
      grid_size: gridSize,
      instances: { ...(existingModule?.instances ?? {}) },
      net_hubs: { ...(existingModule?.net_hubs ?? {}) }
    }

    nodes.forEach((node) => {
      if (node.type === 'instance') {
        const { x, y } = gridFromTopLeft(node, gridSize)
        const existing = moduleLayout.instances[node.id]
        moduleLayout.instances[node.id] = {
          x,
          y,
          orient: existing?.orient ?? 'R0',
          label: existing?.label
        }
      }
      if (node.type === 'hub') {
        const { x, y } = centerFromNode(node, gridSize, HUB_SIZE, HUB_SIZE)
        const existing = moduleLayout.net_hubs[node.id]
        const group = existing?.groups?.[0]
        moduleLayout.net_hubs[node.id] = {
          groups: [
            {
              x,
              y,
              orient: group?.orient,
              label: group?.label
            }
          ]
        }
      }
    })

    nextLayout.modules[moduleId] = moduleLayout
    setLayout(nextLayout)
    vscode?.postMessage({
      type: 'saveLayout',
      payload: {
        moduleId,
        layout: nextLayout
      }
    })
  }, [layout, graph, nodes, gridSize])

  return (
    <div className="app">
      <header className="toolbar">
        <div className="title">ASDL Visualizer — Phase C</div>
        <button className="primary" onClick={onSave} disabled={!layout || !graph}>
          Save Layout
        </button>
      </header>

      <section className="content">
        <div className="canvas">
          {!graph && <p className="muted">Waiting for data from extension…</p>}
          {graph && (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              snapToGrid
              snapGrid={[gridSize, gridSize]}
              defaultEdgeOptions={{
                type: 'step',
                style: { stroke: '#e2e8f0', strokeWidth: 2, strokeLinecap: 'round' }
              }}
              connectionLineType={ConnectionLineType.Step}
              connectionLineStyle={{ stroke: '#e2e8f0', strokeWidth: 2 }}
              className="reactflow"
            >
              <Background gap={gridSize} size={1} />
              <Controls />
            </ReactFlow>
          )}
        </div>
        <aside className="panel diagnostics">
          <h2>Diagnostics</h2>
          {diagnostics.length === 0 && <p className="muted">No diagnostics.</p>}
          {diagnostics.length > 0 && (
            <ul>
              {diagnostics.map((item, index) => (
                <li key={`${item}-${index}`}>{item}</li>
              ))}
            </ul>
          )}
        </aside>
      </section>
    </div>
  )
}

function buildReactFlowGraph(
  graph: GraphPayload,
  moduleLayout: LayoutPayload['modules'][string] | undefined,
  gridSize: number
): { nodes: Array<Node<VisualNodeData>>; edges: Array<Edge> } {
  const instances = graph.instances.map((inst, index) => {
    const placement = moduleLayout?.instances?.[inst.id]
    const gridX = placement?.x ?? index * 4
    const gridY = placement?.y ?? 0
    const symbol = graph.symbols[inst.symbolKey] ?? FALLBACK_SYMBOL
    const baseBody = normalizeSymbolBody(symbol.body)
    const orientSpec = normalizeOrient(placement?.orient)
    const orientationMatrix = buildOrientationMatrix(orientSpec, baseBody)
    const orientedBody = orientBody(baseBody, orientationMatrix)
    const pins = orientPins(computePinPositions(symbol, baseBody), orientationMatrix, orientSpec)
    const glyph = symbol.glyph
      ? {
          src: symbol.glyph.src,
          viewbox: symbol.glyph.viewbox,
          box: orientRect(symbol.glyph.box, orientationMatrix)
        }
      : undefined
    const pos = topLeftFromGrid(gridX, gridY, gridSize)
    return {
      id: inst.id,
      type: 'instance',
      position: pos,
      data: {
        label: inst.label,
        orient: orientSpec.key,
        body: { w: orientedBody.w, h: orientedBody.h },
        pins,
        gridSize,
        glyph
      },
      style: {
        width: orientedBody.w * gridSize,
        height: orientedBody.h * gridSize
      }
    } as Node<InstanceNodeData>
  })

  const hubs = graph.netHubs.map((hub, index) => {
    const placement = moduleLayout?.net_hubs?.[hub.id]?.groups?.[0]
    const gridX = placement?.x ?? (instances.length + 2) * 4
    const gridY = placement?.y ?? index * 4
    const pos = topLeftFromCenter(gridX, gridY, gridSize, HUB_SIZE, HUB_SIZE)
    const orientSpec = normalizeOrient(placement?.orient)
    return {
      id: hub.id,
      type: 'hub',
      position: pos,
      data: { label: hub.label, orient: orientSpec.key, gridSize },
      style: {
        width: HUB_SIZE * gridSize,
        height: HUB_SIZE * gridSize
      }
    } as Node<HubNodeData>
  })

  const nodeIds = new Set([...instances.map((n) => n.id), ...hubs.map((n) => n.id)])
  const edges = graph.edges
    .map((edge) => {
      const { nodeId: source, handleId: sourceHandle } = parseEndpoint(edge.from)
      const target = edge.to
      if (!nodeIds.has(source) || !nodeIds.has(target)) {
        return null
      }
      return {
        id: edge.id,
        source,
        target,
        sourceHandle,
        targetHandle: HUB_HANDLE_ID,
        type: 'step',
        style: { stroke: '#e2e8f0', strokeWidth: 2, strokeLinecap: 'round' }
      } as Edge
    })
    .filter((edge): edge is Edge => Boolean(edge))

  return { nodes: [...instances, ...hubs], edges }
}

function topLeftFromCenter(
  gridX: number,
  gridY: number,
  gridSize: number,
  widthUnits: number,
  heightUnits: number
) {
  const width = widthUnits * gridSize
  const height = heightUnits * gridSize
  const cx = gridX * gridSize
  const cy = gridY * gridSize
  return {
    x: Math.round(cx - width / 2),
    y: Math.round(cy - height / 2)
  }
}

function topLeftFromGrid(gridX: number, gridY: number, gridSize: number) {
  return {
    x: gridX * gridSize,
    y: gridY * gridSize
  }
}

function centerFromNode(
  node: Node,
  gridSize: number,
  widthUnits: number,
  heightUnits: number
) {
  const width = widthUnits * gridSize
  const height = heightUnits * gridSize
  const cx = node.position.x + width / 2
  const cy = node.position.y + height / 2
  return {
    x: Math.round(cx / gridSize),
    y: Math.round(cy / gridSize)
  }
}

function gridFromTopLeft(node: Node, gridSize: number) {
  return {
    x: Math.round(node.position.x / gridSize),
    y: Math.round(node.position.y / gridSize)
  }
}

function normalizeSymbolBody(body: { w?: number; h?: number }) {
  const w =
    typeof body.w === 'number' && Number.isFinite(body.w) && body.w > 0
      ? body.w
      : FALLBACK_SYMBOL.body.w
  const h =
    typeof body.h === 'number' && Number.isFinite(body.h) && body.h > 0
      ? body.h
      : FALLBACK_SYMBOL.body.h
  return { w, h }
}

type Matrix = {
  a: number
  b: number
  c: number
  d: number
  e: number
  f: number
}

const SIDE_ORDER: PinSide[] = ['top', 'right', 'bottom', 'left']

function normalizeOrient(orient?: string): OrientationSpec {
  const key = (orient ?? 'R0').toUpperCase()
  if (key in ORIENT_SPECS) {
    return ORIENT_SPECS[key as Orientation]
  }
  return ORIENT_SPECS.R0
}

function identityMatrix(): Matrix {
  return { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 }
}

function mirrorXMatrix(height: number): Matrix {
  return { a: 1, b: 0, c: 0, d: -1, e: 0, f: height }
}

function mirrorYMatrix(width: number): Matrix {
  return { a: -1, b: 0, c: 0, d: 1, e: width, f: 0 }
}

function rotationMatrix(rotation: OrientationSpec['rotation'], width: number, height: number): Matrix {
  if (rotation === 90) {
    return { a: 0, b: -1, c: 1, d: 0, e: 0, f: width }
  }
  if (rotation === 180) {
    return { a: -1, b: 0, c: 0, d: -1, e: width, f: height }
  }
  if (rotation === 270) {
    return { a: 0, b: 1, c: -1, d: 0, e: height, f: 0 }
  }
  return identityMatrix()
}

function multiplyMatrices(next: Matrix, prev: Matrix): Matrix {
  return {
    a: next.a * prev.a + next.c * prev.b,
    b: next.b * prev.a + next.d * prev.b,
    c: next.a * prev.c + next.c * prev.d,
    d: next.b * prev.c + next.d * prev.d,
    e: next.a * prev.e + next.c * prev.f + next.e,
    f: next.b * prev.e + next.d * prev.f + next.f
  }
}

function applyMatrix(point: { x: number; y: number }, matrix: Matrix) {
  return {
    x: matrix.a * point.x + matrix.c * point.y + matrix.e,
    y: matrix.b * point.x + matrix.d * point.y + matrix.f
  }
}

function buildOrientationMatrix(
  spec: OrientationSpec,
  body: { w: number; h: number }
): Matrix {
  // Screen coords: x→right, y→down. Mirror X flips vertically (y → h - y),
  // mirror Y flips horizontally (x → w - x). Mirrors apply before rotation.
  let matrix = identityMatrix()
  if (spec.mirrorX) {
    matrix = multiplyMatrices(mirrorXMatrix(body.h), matrix)
  }
  if (spec.mirrorY) {
    matrix = multiplyMatrices(mirrorYMatrix(body.w), matrix)
  }
  matrix = multiplyMatrices(rotationMatrix(spec.rotation, body.w, body.h), matrix)
  return matrix
}

function orientRect(
  rect: { x: number; y: number; w: number; h: number },
  matrix: Matrix
): { x: number; y: number; w: number; h: number } {
  const corners = [
    applyMatrix({ x: rect.x, y: rect.y }, matrix),
    applyMatrix({ x: rect.x + rect.w, y: rect.y }, matrix),
    applyMatrix({ x: rect.x, y: rect.y + rect.h }, matrix),
    applyMatrix({ x: rect.x + rect.w, y: rect.y + rect.h }, matrix)
  ]
  const xs = corners.map((pt) => pt.x)
  const ys = corners.map((pt) => pt.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY }
}

function orientBody(body: { w: number; h: number }, matrix: Matrix) {
  return orientRect({ x: 0, y: 0, w: body.w, h: body.h }, matrix)
}

function mirrorSideX(side: PinSide): PinSide {
  if (side === 'top') {
    return 'bottom'
  }
  if (side === 'bottom') {
    return 'top'
  }
  return side
}

function mirrorSideY(side: PinSide): PinSide {
  if (side === 'left') {
    return 'right'
  }
  if (side === 'right') {
    return 'left'
  }
  return side
}

function rotateSide(side: PinSide, rotation: OrientationSpec['rotation']): PinSide {
  if (rotation === 0) {
    return side
  }
  const index = SIDE_ORDER.indexOf(side)
  const offset = rotation === 90 ? 3 : rotation === 180 ? 2 : 1
  return SIDE_ORDER[(index + offset) % SIDE_ORDER.length]
}

function orientSide(side: PinSide, spec: OrientationSpec): PinSide {
  let oriented = side
  if (spec.mirrorX) {
    oriented = mirrorSideX(oriented)
  }
  if (spec.mirrorY) {
    oriented = mirrorSideY(oriented)
  }
  oriented = rotateSide(oriented, spec.rotation)
  return oriented
}

function orientPins(pins: PinPosition[], matrix: Matrix, spec: OrientationSpec): PinPosition[] {
  return pins.map((pin) => {
    const oriented = applyMatrix({ x: pin.x, y: pin.y }, matrix)
    return {
      ...pin,
      x: oriented.x,
      y: oriented.y,
      side: orientSide(pin.side, spec)
    }
  })
}

function orientVector(point: { x: number; y: number }, spec: OrientationSpec) {
  let { x, y } = point
  if (spec.mirrorX) {
    y = -y
  }
  if (spec.mirrorY) {
    x = -x
  }
  if (spec.rotation === 90) {
    return { x: y, y: -x }
  }
  if (spec.rotation === 180) {
    return { x: -x, y: -y }
  }
  if (spec.rotation === 270) {
    return { x: -y, y: x }
  }
  return { x, y }
}

function positionFromSide(side: PinSide): Position {
  if (side === 'left') {
    return Position.Left
  }
  if (side === 'right') {
    return Position.Right
  }
  if (side === 'top') {
    return Position.Top
  }
  return Position.Bottom
}

function computePinPositions(symbol: SymbolDefinition, body: { w: number; h: number }) {
  const pins: PinPosition[] = []
  const pinConfig = symbol.pins ?? {}

  const pushPins = (side: PinSide, entries: Array<SymbolPin | null> | undefined, edge: number) => {
    if (!entries || entries.length === 0) {
      return
    }
    const span = entries.length > 1 ? entries.length - 1 : 0
    const start = Math.floor((edge - span) / 2)
    entries.forEach((entry, index) => {
      if (!entry) {
        return
      }
      const along = start + index + entry.offset
      const position =
        side === 'left'
          ? { x: 0, y: along }
          : side === 'right'
            ? { x: body.w, y: along }
            : side === 'top'
              ? { x: along, y: 0 }
              : { x: along, y: body.h }
      pins.push({ id: entry.name, name: entry.name, side, visible: entry.visible, ...position })
    })
  }

  pushPins('left', pinConfig.left, body.h)
  pushPins('right', pinConfig.right, body.h)
  pushPins('top', pinConfig.top, body.w)
  pushPins('bottom', pinConfig.bottom, body.w)

  return pins
}

function parseEndpoint(value: string): { nodeId: string; handleId?: string } {
  const splitIndex = value.lastIndexOf('.')
  if (splitIndex > 0 && splitIndex < value.length - 1) {
    return { nodeId: value.slice(0, splitIndex), handleId: value.slice(splitIndex + 1) }
  }
  return { nodeId: value }
}

function InstanceNodeComponent({ data }: NodeProps<InstanceNodeData>) {
  const glyph = data.glyph
  const glyphStyle = glyph
    ? {
        left: glyph.box.x * data.gridSize,
        top: glyph.box.y * data.gridSize,
        width: glyph.box.w * data.gridSize,
        height: glyph.box.h * data.gridSize
      }
    : undefined
  return (
    <div className="node instance-node">
      {glyph && (
        <svg
          className="glyph-frame"
          style={glyphStyle}
          viewBox={glyph.viewbox}
          preserveAspectRatio="xMidYMid meet"
        >
          <image
            href={glyph.src}
            width="100%"
            height="100%"
            preserveAspectRatio="xMidYMid meet"
          />
        </svg>
      )}
      {data.pins.map((pin) => {
        const style =
          pin.side === 'left' || pin.side === 'right'
            ? { top: pin.y * data.gridSize }
            : { left: pin.x * data.gridSize }
        return (
          <Handle
            key={`${pin.id}-${pin.side}`}
            id={pin.id}
            type="source"
            position={positionFromSide(pin.side)}
            style={style}
            className="pin-handle"
          />
        )
      })}
      <div className="node-title">{data.label}</div>
      <div className="node-subtitle">{data.orient}</div>
    </div>
  )
}

function HubNodeComponent({ data }: NodeProps<HubNodeData>) {
  const orientSpec = normalizeOrient(data.orient)
  const hubCenter = HUB_SIZE / 2
  const handleOffset = orientVector({ x: hubCenter, y: 0 }, orientSpec)
  const handleSide = orientSide('right', orientSpec)
  return (
    <div className="node hub-node">
      <Handle
        type="target"
        id={HUB_HANDLE_ID}
        position={positionFromSide(handleSide)}
        style={{
          left: (hubCenter + handleOffset.x) * data.gridSize,
          top: (hubCenter + handleOffset.y) * data.gridSize,
          transform: 'translate(-50%, -50%)'
        }}
        className="hub-handle"
      />
      <div className="hub-dot" />
      <div className="hub-label">{data.label}</div>
    </div>
  )
}
