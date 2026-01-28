import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ReactFlow, {
  Background,
  ConnectionLineType,
  Controls,
  Position,
  Handle,
  useEdgesState,
  useNodesState,
  useUpdateNodeInternals,
  type Edge,
  type Node,
  type NodeProps,
  type NodeTypes,
  type ReactFlowInstance
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

type InstanceNodeData = {
  label: string
  orient: string
  body: { w: number; h: number }
  pins: PinPosition[]
  gridSize: number
  glyph?: SymbolGlyph
}

type HubNodeData = {
  label: string
}

type VisualNodeData = InstanceNodeData | HubNodeData

type PinSide = 'top' | 'bottom' | 'left' | 'right'
type Orient = 'R0' | 'R90' | 'R180' | 'R270' | 'MX' | 'MY' | 'MXR90' | 'MYR90'

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
  const reactFlowRef = useRef<ReactFlowInstance | null>(null)
  const [fitViewToken, setFitViewToken] = useState(0)
  const graphRef = useRef<GraphPayload | null>(null)

  const nodeTypes = useMemo<NodeTypes>(() => ({
    instance: InstanceNodeComponent,
    hub: HubNodeComponent
  }), [])

  useEffect(() => {
    const handleMessage = (event: MessageEvent<WebviewMessage>) => {
      const message = event.data
      if (message.type === 'loadGraph') {
        const nextGraph = message.payload.graph
        const prevGraph = graphRef.current
        const isSameModule = prevGraph?.moduleId === nextGraph.moduleId
        const isSameShape =
          prevGraph &&
          prevGraph.instances.length === nextGraph.instances.length &&
          prevGraph.netHubs.length === nextGraph.netHubs.length &&
          prevGraph.edges.length === nextGraph.edges.length
        const shouldRebuild = !prevGraph || !isSameModule || !isSameShape

        if (shouldRebuild) {
          setGraph(nextGraph)
          setLayout(message.payload.layout)
          graphRef.current = nextGraph
          const moduleLayout = message.payload.layout.modules[nextGraph.moduleId]
          const grid = moduleLayout?.grid_size ?? DEFAULT_GRID_SIZE
          setGridSize(grid)
          const { nodes: rfNodes, edges: rfEdges } = buildReactFlowGraph(
            nextGraph,
            moduleLayout,
            grid
          )
          setNodes(rfNodes)
          setEdges(rfEdges)
          setFitViewToken((token) => token + 1)
        }
        if (message.payload.diagnostics) {
          setDiagnostics(message.payload.diagnostics)
        }
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

  useEffect(() => {
    if (fitViewToken === 0) {
      return
    }
    const instance = reactFlowRef.current
    if (!instance) {
      return
    }
    const handle = requestAnimationFrame(() => {
      instance.fitView({ padding: 0.2 })
    })
    return () => cancelAnimationFrame(handle)
  }, [fitViewToken])

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
              onInit={(instance) => {
                reactFlowRef.current = instance
              }}
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
    const orient = normalizeOrient(placement?.orient)
    const symbol = graph.symbols[inst.symbolKey] ?? FALLBACK_SYMBOL
    const body = normalizeSymbolBody(symbol.body)
    const pins = computePinPositions(symbol, body)
    const pos = topLeftFromGrid(gridX, gridY, gridSize)
    const orientedBody = computeOrientData(body.w, body.h, orient)
    return {
      id: inst.id,
      type: 'instance',
      position: pos,
      data: {
        label: inst.label,
        orient,
        body,
        pins,
        gridSize,
        glyph: symbol.glyph
      },
      style: {
        width: orientedBody.width * gridSize,
        height: orientedBody.height * gridSize
      }
    } as Node<InstanceNodeData>
  })

  const hubs = graph.netHubs.map((hub, index) => {
    const placement = moduleLayout?.net_hubs?.[hub.id]?.groups?.[0]
    const gridX = placement?.x ?? (instances.length + 2) * 4
    const gridY = placement?.y ?? index * 4
    const pos = topLeftFromCenter(gridX, gridY, gridSize, HUB_SIZE, HUB_SIZE)
    return {
      id: hub.id,
      type: 'hub',
      position: pos,
      data: { label: hub.label },
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

function normalizeOrient(value: string | undefined): Orient {
  const raw = (value ?? 'R0').toUpperCase()
  if (
    raw === 'R0' ||
    raw === 'R90' ||
    raw === 'R180' ||
    raw === 'R270' ||
    raw === 'MX' ||
    raw === 'MY' ||
    raw === 'MXR90' ||
    raw === 'MYR90'
  ) {
    return raw as Orient
  }
  return 'R0'
}

type OrientMatrix = { a: number; b: number; c: number; d: number }
type OrientData = OrientMatrix & {
  tx: number
  ty: number
  width: number
  height: number
  transform: string
}

function orientMatrix(orient: Orient): OrientMatrix {
  const mirrorX = orient.startsWith('MX')
  const mirrorY = orient.startsWith('MY')
  const rotation = orient.endsWith('R90')
    ? 90
    : orient.endsWith('R180')
      ? 180
      : orient.endsWith('R270')
        ? 270
        : 0
  const sx = mirrorY ? -1 : 1
  const sy = mirrorX ? -1 : 1

  const r =
    rotation === 90
      ? { r11: 0, r12: 1, r21: -1, r22: 0 }
      : rotation === 180
        ? { r11: -1, r12: 0, r21: 0, r22: -1 }
        : rotation === 270
          ? { r11: 0, r12: -1, r21: 1, r22: 0 }
          : { r11: 1, r12: 0, r21: 0, r22: 1 }

  return {
    a: r.r11 * sx,
    b: r.r21 * sx,
    c: r.r12 * sy,
    d: r.r22 * sy
  }
}

function computeOrientData(w: number, h: number, orient: Orient): OrientData {
  const { a, b, c, d } = orientMatrix(orient)
  const points = [
    { x: 0, y: 0 },
    { x: w, y: 0 },
    { x: 0, y: h },
    { x: w, y: h }
  ].map((p) => ({ x: a * p.x + c * p.y, y: b * p.x + d * p.y }))
  const xs = points.map((p) => p.x)
  const ys = points.map((p) => p.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const tx = -minX
  const ty = -minY
  return {
    a,
    b,
    c,
    d,
    tx,
    ty,
    width: maxX - minX,
    height: maxY - minY,
    transform: `matrix(${a}, ${b}, ${c}, ${d}, ${tx}, ${ty})`
  }
}

function applyOrientPoint(x: number, y: number, orient: OrientData): { x: number; y: number } {
  return { x: orient.a * x + orient.c * y + orient.tx, y: orient.b * x + orient.d * y + orient.ty }
}

function mapPinSide(side: PinSide, orient: OrientData): PinSide {
  const vector =
    side === 'left'
      ? { x: -1, y: 0 }
      : side === 'right'
        ? { x: 1, y: 0 }
        : side === 'top'
          ? { x: 0, y: -1 }
          : { x: 0, y: 1 }
  const x = orient.a * vector.x + orient.c * vector.y
  const y = orient.b * vector.x + orient.d * vector.y
  if (Math.abs(x) >= Math.abs(y)) {
    return x < 0 ? 'left' : 'right'
  }
  return y < 0 ? 'top' : 'bottom'
}

function parseEndpoint(value: string): { nodeId: string; handleId?: string } {
  const splitIndex = value.lastIndexOf('.')
  if (splitIndex > 0 && splitIndex < value.length - 1) {
    return { nodeId: value.slice(0, splitIndex), handleId: value.slice(splitIndex + 1) }
  }
  return { nodeId: value }
}

function InstanceNodeComponent({ id, data }: NodeProps<InstanceNodeData>) {
  const updateNodeInternals = useUpdateNodeInternals()
  const orient = normalizeOrient(data.orient)
  const baseWidth = data.body.w * data.gridSize
  const baseHeight = data.body.h * data.gridSize
  const orientData = computeOrientData(baseWidth, baseHeight, orient)

  const orientedPins = useMemo(() => {
    return data.pins.map((pin) => {
      const x = pin.x * data.gridSize
      const y = pin.y * data.gridSize
      const { x: ox, y: oy } = applyOrientPoint(x, y, orientData)
      const side = mapPinSide(pin.side, orientData)
      return { ...pin, x: ox, y: oy, side }
    })
  }, [data.pins, data.gridSize, orientData])

  useEffect(() => {
    updateNodeInternals(id)
  }, [id, orient, updateNodeInternals])

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
      <div
        className="symbol-layer"
        style={{
          width: baseWidth,
          height: baseHeight,
          transformOrigin: '0 0',
          transform: orientData.transform
        }}
      >
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
      </div>
      {orientedPins.map((pin) => {
        const position =
          pin.side === 'left'
            ? Position.Left
            : pin.side === 'right'
              ? Position.Right
              : pin.side === 'top'
                ? Position.Top
                : Position.Bottom
        return (
          <Handle
            key={`${pin.id}-${pin.side}`}
            id={pin.id}
            type="source"
            position={position}
            style={{ left: pin.x, top: pin.y, transform: 'translate(-50%, -50%)' }}
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
  return (
    <div className="node hub-node">
      <Handle
        type="target"
        id={HUB_HANDLE_ID}
        position={Position.Top}
        style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
        className="hub-handle"
      />
      <div className="hub-dot" />
      <div className="hub-label">{data.label}</div>
    </div>
  )
}
