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
  layoutKey?: string
}

type NetHubNode = {
  id: string
  label: string
  layoutKey?: string
}

type GraphPayload = {
  moduleId: string
  instances: InstanceNode[]
  netHubs: NetHubNode[]
  edges: Array<{ id: string; from: string; to: string; conn_label?: string }>
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
  connect_by_label?: boolean
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
      net_hubs: Record<string, Record<string, Placement>>
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
const EDGE_STEP_OFFSET_UNITS = 0.8
const PIN_LABEL_INSET_RATIO = 0.6
const PIN_LABEL_INSET_MIN_PX = 6
const FALLBACK_SYMBOL: SymbolDefinition = {
  body: { w: 6, h: 4 },
  pins: { left: [] }
}

type InstanceNodeData = {
  label: string
  orient: string
  body: { w: number; h: number }
  pins: PinPosition[]
  netLabels: Record<string, string | null>
  gridSize: number
  glyph?: SymbolGlyph
}

type HubNodeData = {
  label: string
  orient: string
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
  connectByLabel: boolean
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
    const instanceLayoutKeys = new Map(
      graph.instances.map((inst) => [inst.id, inst.layoutKey ?? inst.id])
    )
    const hubLayoutKeys = new Map(
      graph.netHubs.map((hub) => [hub.id, hub.layoutKey ?? hub.id])
    )
    const moduleLayout = {
      grid_size: gridSize,
      instances: {},
      net_hubs: {}
    }

    nodes.forEach((node) => {
      if (node.type === 'instance') {
        const { x, y } = gridFromTopLeft(node, gridSize)
        const layoutKey = instanceLayoutKeys.get(node.id) ?? node.id
        const existing =
          existingModule?.instances?.[layoutKey] ?? existingModule?.instances?.[node.id]
        const orient = normalizeOrient((node.data as InstanceNodeData).orient)
        moduleLayout.instances[layoutKey] = {
          x,
          y,
          orient,
          label: existing?.label
        }
      }
      if (node.type === 'hub') {
        const { x, y } = centerFromNode(node, gridSize, HUB_SIZE, HUB_SIZE)
        const layoutKey = hubLayoutKeys.get(node.id) ?? node.id
        const existing =
          existingModule?.net_hubs?.[layoutKey] ?? existingModule?.net_hubs?.[node.id]
        const sanitized = sanitizeHubLayout(existing)
        const entry = firstHubEntry(sanitized)
        const firstKey = entry?.key ?? 'hub1'
        const firstHub = entry?.placement
        const orient = normalizeOrient((node.data as HubNodeData).orient)
        moduleLayout.net_hubs[layoutKey] = {
          ...sanitized,
          [firstKey]: {
            x,
            y,
            orient,
            label: firstHub?.label
          }
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
                type: 'smoothstep',
                style: { stroke: '#e2e8f0', strokeWidth: 2, strokeLinecap: 'round' },
                pathOptions: { offset: gridSize * EDGE_STEP_OFFSET_UNITS }
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
  const netLabelById = new Map(
    graph.netHubs.map((hub) => [hub.id, hub.label || hub.id])
  )
  const connectByLabelPins = new Map<string, Set<string>>()
  const instances = graph.instances.map((inst, index) => {
    const layoutKey = inst.layoutKey ?? inst.id
    const placement =
      moduleLayout?.instances?.[layoutKey] ?? moduleLayout?.instances?.[inst.id]
    const gridX = placement?.x ?? index * 4
    const gridY = placement?.y ?? 0
    const orient = normalizeOrient(placement?.orient)
    const symbol = graph.symbols[inst.symbolKey] ?? FALLBACK_SYMBOL
    const body = normalizeSymbolBody(symbol.body)
    const pins = computePinPositions(symbol, body)
    const pinLabelSet = new Set<string>()
    pins.forEach((pin) => {
      if (pin.connectByLabel) {
        pinLabelSet.add(pin.id)
      }
    })
    connectByLabelPins.set(inst.id, pinLabelSet)
    const netLabels = buildNetLabelMap(inst.id, pins, graph.edges, netLabelById)
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
        netLabels,
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
    const layoutKey = hub.layoutKey ?? hub.id
    const placement =
      firstHubPlacement(moduleLayout?.net_hubs?.[layoutKey]) ??
      firstHubPlacement(moduleLayout?.net_hubs?.[hub.id])
    const gridX = placement?.x ?? (instances.length + 2) * 4
    const gridY = placement?.y ?? index * 4
    const pos = topLeftFromCenter(gridX, gridY, gridSize, HUB_SIZE, HUB_SIZE)
    const orient = normalizeOrient(placement?.orient)
    return {
      id: hub.id,
      type: 'hub',
      position: pos,
      data: { label: hub.label, orient },
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
      if (sourceHandle) {
        const suppressed = connectByLabelPins.get(source)?.has(sourceHandle)
        if (suppressed) {
          return null
        }
      }
      return {
        id: edge.id,
        source,
        target,
        sourceHandle,
        targetHandle: HUB_HANDLE_ID,
        type: 'smoothstep',
        pathOptions: { offset: gridSize * EDGE_STEP_OFFSET_UNITS },
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

function isPlacement(value: unknown): value is Placement {
  if (!value || typeof value !== 'object') {
    return false
  }
  const candidate = value as Placement
  return Number.isFinite(candidate.x) && Number.isFinite(candidate.y)
}

function sanitizeHubLayout(
  hubLayout: Record<string, Placement> | undefined
): Record<string, Placement> {
  if (!hubLayout) {
    return {}
  }
  const sanitized: Record<string, Placement> = {}
  for (const [key, placement] of Object.entries(hubLayout)) {
    if (isPlacement(placement)) {
      sanitized[key] = placement
    }
  }
  return sanitized
}

function firstHubEntry(
  hubLayout: Record<string, Placement> | undefined
): { key: string; placement: Placement } | undefined {
  if (!hubLayout) {
    return undefined
  }
  for (const [key, placement] of Object.entries(hubLayout)) {
    if (isPlacement(placement)) {
      return { key, placement }
    }
  }
  return undefined
}

function firstHubPlacement(hubLayout: Record<string, Placement> | undefined): Placement | undefined {
  return firstHubEntry(hubLayout)?.placement
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
      pins.push({
        id: entry.name,
        name: entry.name,
        side,
        visible: entry.visible,
        connectByLabel: entry.connect_by_label === true,
        ...position
      })
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

function mapVectorToSide(x: number, y: number): PinSide {
  if (Math.abs(x) >= Math.abs(y)) {
    return x < 0 ? 'left' : 'right'
  }
  return y < 0 ? 'top' : 'bottom'
}

function positionFromSide(side: PinSide): Position {
  return side === 'left'
    ? Position.Left
    : side === 'right'
      ? Position.Right
      : side === 'top'
        ? Position.Top
        : Position.Bottom
}

function parseEndpoint(value: string): { nodeId: string; handleId?: string } {
  const splitIndex = value.lastIndexOf('.')
  if (splitIndex > 0 && splitIndex < value.length - 1) {
    return { nodeId: value.slice(0, splitIndex), handleId: value.slice(splitIndex + 1) }
  }
  return { nodeId: value }
}

function buildNetLabelMap(
  instanceId: string,
  pins: PinPosition[],
  edges: GraphPayload['edges'],
  netLabelById: Map<string, string>
): Record<string, string | null> {
  const labelsByPin = new Map<string, { numeric: string[]; nets: string[] }>()
  edges.forEach((edge) => {
    const { nodeId, handleId } = parseEndpoint(edge.from)
    if (nodeId !== instanceId || !handleId) {
      return
    }
    const entry = labelsByPin.get(handleId) ?? { numeric: [], nets: [] }
    const numericLabel = edge.conn_label?.trim()
    if (numericLabel) {
      entry.numeric.push(numericLabel)
    } else {
      const netLabel = netLabelById.get(edge.to)
      if (netLabel) {
        entry.nets.push(netLabel)
      }
    }
    labelsByPin.set(handleId, entry)
  })

  const netLabels: Record<string, string | null> = {}
  pins.forEach((pin) => {
    const entry = labelsByPin.get(pin.id)
    const numericLabel = joinLabels(entry?.numeric ?? [])
    if (numericLabel) {
      netLabels[pin.id] = numericLabel
      return
    }
    if (pin.connectByLabel) {
      netLabels[pin.id] = joinLabels(entry?.nets ?? [])
      return
    }
    netLabels[pin.id] = null
  })

  return netLabels
}

function joinLabels(labels: string[]): string | null {
  const seen = new Set<string>()
  const ordered: string[] = []
  labels.forEach((label) => {
    const trimmed = label.trim()
    if (!trimmed || seen.has(trimmed)) {
      return
    }
    seen.add(trimmed)
    ordered.push(trimmed)
  })
  return ordered.length > 0 ? ordered.join(';') : null
}

function pinLabelInset(gridSize: number): number {
  return Math.max(PIN_LABEL_INSET_MIN_PX, Math.round(gridSize * PIN_LABEL_INSET_RATIO))
}

function computePinNamePosition(
  x: number,
  y: number,
  side: PinSide,
  inset: number
): { x: number; y: number } {
  if (side === 'left') {
    return { x: x + inset, y }
  }
  if (side === 'right') {
    return { x: x - inset, y }
  }
  if (side === 'top') {
    return { x, y: y + inset }
  }
  return { x, y: y - inset }
}

function computeNetLabelPosition(
  x: number,
  y: number,
  side: PinSide,
  inset: number
): { x: number; y: number } {
  if (side === 'left') {
    return { x: x - inset, y }
  }
  if (side === 'right') {
    return { x: x + inset, y }
  }
  if (side === 'top') {
    return { x, y: y - inset }
  }
  return { x, y: y + inset }
}

function InstanceNodeComponent({ id, data }: NodeProps<InstanceNodeData>) {
  const updateNodeInternals = useUpdateNodeInternals()
  const orient = normalizeOrient(data.orient)
  const baseWidth = data.body.w * data.gridSize
  const baseHeight = data.body.h * data.gridSize
  const orientData = computeOrientData(baseWidth, baseHeight, orient)

  const orientedPins = useMemo(() => {
    const inset = pinLabelInset(data.gridSize)
    return data.pins.map((pin) => {
      const x = pin.x * data.gridSize
      const y = pin.y * data.gridSize
      const { x: ox, y: oy } = applyOrientPoint(x, y, orientData)
      const side = mapPinSide(pin.side, orientData)
      const nameText = pin.visible ? pin.name : null
      const namePos = nameText ? computePinNamePosition(ox, oy, side, inset) : null
      const netLabelText = data.netLabels[pin.id] ?? null
      const netLabelPos = netLabelText ? computeNetLabelPosition(ox, oy, side, inset) : null
      return { ...pin, x: ox, y: oy, side, nameText, namePos, netLabelText, netLabelPos }
    })
  }, [data.pins, data.gridSize, data.netLabels, orientData])

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
        const position = positionFromSide(pin.side)
        return (
          <React.Fragment key={`${pin.id}-${pin.side}`}>
            <Handle
              id={pin.id}
              type="source"
              position={position}
              style={{ left: pin.x, top: pin.y, transform: 'translate(-50%, -50%)' }}
              className="pin-handle"
            />
            {pin.nameText && pin.namePos && (
              <div
                className={`pin-name pin-name--${pin.side}`}
                style={{ left: pin.namePos.x, top: pin.namePos.y }}
              >
                {pin.nameText}
              </div>
            )}
            {pin.netLabelText && pin.netLabelPos && (
              <div
                className={`net-label net-label--${pin.side}`}
                style={{ left: pin.netLabelPos.x, top: pin.netLabelPos.y }}
              >
                {pin.netLabelText}
              </div>
            )}
          </React.Fragment>
        )
      })}
      <div className="node-title">{data.label}</div>
      <div className="node-subtitle">{data.orient}</div>
    </div>
  )
}

function HubNodeComponent({ data }: NodeProps<HubNodeData>) {
  const orient = normalizeOrient(data.orient)
  const { a, b } = orientMatrix(orient)
  const handlePosition = positionFromSide(mapVectorToSide(a, b))
  return (
    <div className="node hub-node">
      <Handle
        type="target"
        id={HUB_HANDLE_ID}
        position={handlePosition}
        style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
        className="hub-handle"
      />
      <div className="hub-dot" />
      <div className="hub-label">{data.label}</div>
    </div>
  )
}
