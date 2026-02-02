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

type GroupSlice = {
  start: number
  count: number
  label?: string | null
}

type SchematicHints = {
  net_groups: Record<string, GroupSlice[]>
  hub_group_index: number
}

type GraphPayload = {
  moduleId: string
  instances: InstanceNode[]
  netHubs: NetHubNode[]
  edges: Array<{ id: string; from: string; to: string; conn_label?: string }>
  symbols: Record<string, SymbolDefinition>
  schematic_hints?: SchematicHints | null
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

type NetTopology = 'star' | 'mst' | 'trunk'

type NetHubEntry = {
  topology?: NetTopology
  hubs: Record<string, Placement>
}

type NetHubLayout = NetHubEntry | Record<string, Placement>

type LayoutPayload = {
  schema_version: number
  modules: Record<
    string,
    {
      grid_size?: number
      instances: Record<string, Placement>
      net_hubs: Record<string, NetHubLayout>
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
const DEFAULT_TOPOLOGY: NetTopology = 'star'
const HUB_SIZE = 2
const HUB_HANDLE_ID = 'hub'
const JUNCTION_SIZE = 0.6
const JUNCTION_HANDLE_ID = 'junction'
const EDGE_STEP_OFFSET_UNITS = 0.8
const EDGE_STYLE = { stroke: '#e2e8f0', strokeWidth: 2, strokeLinecap: 'round' }
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
  netId: string
  hubKey: string
  layoutKey: string
}

type JunctionNodeData = {
  kind: 'junction'
}

type VisualNodeData = InstanceNodeData | HubNodeData | JunctionNodeData

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

type RoutedPin = {
  x: number
  y: number
  side: PinSide
  connectByLabel: boolean
}

type RoutedEndpoint = {
  id: string
  netId: string
  instanceId: string
  pinId: string
  connLabel?: string
  order: number
  x: number
  y: number
  connectByLabel: boolean
}

type HubGroupInfo = {
  nodeId: string
  hubKey: string
  layoutKey: string
  orient: Orient
  center: { x: number; y: number }
}

type NetHubInfo = {
  topology: NetTopology
  groups: HubGroupInfo[]
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
    hub: HubNodeComponent,
    junction: JunctionNodeComponent
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
    } as LayoutPayload['modules'][string]

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
        const hubData = node.data as HubNodeData
        const layoutKey =
          hubData.layoutKey ??
          hubLayoutKeys.get(hubData.netId) ??
          hubData.netId ??
          node.id
        const existing =
          existingModule?.net_hubs?.[layoutKey] ??
          existingModule?.net_hubs?.[hubData.netId]
        const normalized = normalizeNetHubEntry(existing)
        const fallbackEntry = firstHubEntry(normalized.hubs)
        const hubKey = hubData.hubKey ?? fallbackEntry?.key ?? 'hub1'
        const hubPlacement = normalized.hubs[hubKey] ?? fallbackEntry?.placement
        const orient = normalizeOrient(hubData.orient)
        moduleLayout.net_hubs[layoutKey] = {
          topology: normalized.topology,
          hubs: {
            ...normalized.hubs,
            [hubKey]: {
              x,
              y,
              orient,
              label: hubPlacement?.label
            }
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
                style: EDGE_STYLE,
                pathOptions: { offset: gridSize * EDGE_STEP_OFFSET_UNITS }
              }}
              connectionLineType={ConnectionLineType.Step}
              connectionLineStyle={EDGE_STYLE}
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
  const routedPins = new Map<string, Map<string, RoutedPin>>()
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
    const netLabels = buildNetLabelMap(inst.id, pins, graph.edges, netLabelById)
    const pos = topLeftFromGrid(gridX, gridY, gridSize)
    const orientedBody = computeOrientData(body.w, body.h, orient)
    const orientData = computeOrientData(body.w * gridSize, body.h * gridSize, orient)
    const pinMap = new Map<string, RoutedPin>()
    pins.forEach((pin) => {
      const { x: ox, y: oy } = applyOrientPoint(
        pin.x * gridSize,
        pin.y * gridSize,
        orientData
      )
      const side = mapPinSide(pin.side, orientData)
      pinMap.set(pin.id, {
        x: pos.x + ox,
        y: pos.y + oy,
        side,
        connectByLabel: pin.connectByLabel
      })
    })
    routedPins.set(inst.id, pinMap)
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

  const hubs: Array<Node<HubNodeData>> = []
  const hubInfoByNet = new Map<string, NetHubInfo>()
  let hubRowIndex = 0

  graph.netHubs.forEach((hub, index) => {
    const layoutKey = hub.layoutKey ?? hub.id
    const rawEntry =
      moduleLayout?.net_hubs?.[layoutKey] ?? moduleLayout?.net_hubs?.[hub.id]
    const normalized = normalizeNetHubEntry(rawEntry)
    const groupSlices = graph.schematic_hints?.net_groups?.[hub.id]
    const groupCount =
      Array.isArray(groupSlices) && groupSlices.length > 0 ? groupSlices.length : 1
    const hubEntries = Object.entries(normalized.hubs).slice(0, groupCount)
    const groups: HubGroupInfo[] = []

    for (let groupIndex = 0; groupIndex < groupCount; groupIndex += 1) {
      const [hubKey, placement] = hubEntries[groupIndex] ?? [
        `hub${groupIndex + 1}`,
        undefined
      ]
      const gridX = placement?.x ?? (instances.length + 2) * 4
      const gridY = placement?.y ?? (hubRowIndex + groupIndex) * 4
      const pos = topLeftFromCenter(gridX, gridY, gridSize, HUB_SIZE, HUB_SIZE)
      const orient = normalizeOrient(placement?.orient)
      const nodeId = `${hub.id}::${hubKey}`
      hubs.push({
        id: nodeId,
        type: 'hub',
        position: pos,
        data: { label: hub.label, orient, netId: hub.id, hubKey, layoutKey },
        style: {
          width: HUB_SIZE * gridSize,
          height: HUB_SIZE * gridSize
        }
      })
      groups.push({
        nodeId,
        hubKey,
        layoutKey,
        orient,
        center: { x: gridX * gridSize, y: gridY * gridSize }
      })
    }
    const topology = normalized.topology ?? DEFAULT_TOPOLOGY
    hubInfoByNet.set(hub.id, { topology, groups })
    hubRowIndex += groupCount
  })

  const endpointsByNet = collectRoutedEndpoints(graph.edges, routedPins)
  const junctionNodes: Array<Node<JunctionNodeData>> = []
  const edges: Edge[] = []
  let edgeIndex = 0
  let junctionIndex = 0

  const makeEdge = (
    source: string,
    target: string,
    sourceHandle: string | undefined,
    targetHandle: string | undefined
  ) => ({
    id: `edge-${edgeIndex++}`,
    source,
    target,
    sourceHandle,
    targetHandle,
    type: 'smoothstep',
    pathOptions: { offset: gridSize * EDGE_STEP_OFFSET_UNITS },
    style: EDGE_STYLE
  })

  const makeJunctionNode = (centerX: number, centerY: number) => {
    const nodeId = `junction-${junctionIndex++}`
    const pos = topLeftFromCenter(
      centerX / gridSize,
      centerY / gridSize,
      gridSize,
      JUNCTION_SIZE,
      JUNCTION_SIZE
    )
    junctionNodes.push({
      id: nodeId,
      type: 'junction',
      position: pos,
      data: { kind: 'junction' },
      draggable: false,
      selectable: false,
      style: {
        width: JUNCTION_SIZE * gridSize,
        height: JUNCTION_SIZE * gridSize
      }
    })
    return nodeId
  }

  graph.netHubs.forEach((hub) => {
    const netId = hub.id
    const netInfo = hubInfoByNet.get(netId)
    if (!netInfo || netInfo.groups.length === 0) {
      return
    }
    const topology = netInfo.topology ?? DEFAULT_TOPOLOGY
    const groupSlices = graph.schematic_hints?.net_groups?.[netId]
    const groupCount = netInfo.groups.length
    const groupedEndpoints = splitEndpointsByGroups(
      endpointsByNet.get(netId) ?? [],
      groupSlices,
      groupCount
    )

    for (let groupIndex = 0; groupIndex < groupCount; groupIndex += 1) {
      const hubGroup = netInfo.groups[groupIndex]
      if (!hubGroup) {
        continue
      }
      const groupEndpoints = groupedEndpoints[groupIndex] ?? []
      const routable = groupEndpoints.filter((endpoint) => !endpoint.connectByLabel)
      if (topology === 'mst') {
        edges.push(
          ...buildMstEdges(
            routable,
            hubGroup,
            makeEdge
          )
        )
        continue
      }
      if (topology === 'trunk') {
        const trunkResult = buildTrunkEdges(
          routable,
          hubGroup,
          makeEdge,
          makeJunctionNode
        )
        edges.push(...trunkResult)
        continue
      }
      edges.push(
        ...routable.map((endpoint) =>
          makeEdge(
            endpoint.instanceId,
            hubGroup.nodeId,
            endpoint.pinId,
            HUB_HANDLE_ID
          )
        )
      )
    }
  })

  return { nodes: [...instances, ...hubs, ...junctionNodes], edges }
}

function collectRoutedEndpoints(
  edges: GraphPayload['edges'],
  routedPins: Map<string, Map<string, RoutedPin>>
): Map<string, RoutedEndpoint[]> {
  const endpointsByNet = new Map<string, RoutedEndpoint[]>()
  edges.forEach((edge) => {
    const { nodeId, handleId } = parseEndpoint(edge.from)
    if (!handleId) {
      return
    }
    const pinMap = routedPins.get(nodeId)
    const pin = pinMap?.get(handleId)
    if (!pin) {
      return
    }
    const netId = edge.to
    const list = endpointsByNet.get(netId) ?? []
    list.push({
      id: edge.id,
      netId,
      instanceId: nodeId,
      pinId: handleId,
      connLabel: edge.conn_label,
      order: list.length,
      x: pin.x,
      y: pin.y,
      connectByLabel: pin.connectByLabel
    })
    endpointsByNet.set(netId, list)
  })
  return endpointsByNet
}

function splitEndpointsByGroups(
  endpoints: RoutedEndpoint[],
  groupSlices: GroupSlice[] | undefined,
  groupCount: number
): RoutedEndpoint[][] {
  const groups = Array.from({ length: groupCount }, () => [] as RoutedEndpoint[])
  if (!groupSlices || groupSlices.length === 0) {
    if (groups.length > 0) {
      groups[0] = endpoints.slice()
    }
    return groups
  }

  const used = new Set<number>()
  groupSlices.forEach((slice, index) => {
    if (index >= groupCount) {
      return
    }
    if (!slice || typeof slice.start !== 'number' || typeof slice.count !== 'number') {
      return
    }
    const start = Math.max(0, Math.floor(slice.start))
    const count = Math.max(0, Math.floor(slice.count))
    if (count === 0 || start >= endpoints.length) {
      return
    }
    const end = Math.min(endpoints.length, start + count)
    groups[index] = endpoints.slice(start, end)
    for (let idx = start; idx < end; idx += 1) {
      used.add(idx)
    }
  })

  if (used.size < endpoints.length && groups.length > 0) {
    const remainder = endpoints.filter((_, index) => !used.has(index))
    if (remainder.length > 0) {
      const targetIndex = Math.max(0, groups.length - 1)
      groups[targetIndex] = [...groups[targetIndex], ...remainder]
    }
  }

  return groups
}

type MstNode = {
  kind: 'hub' | 'endpoint'
  key: number
  x: number
  y: number
  endpoint?: RoutedEndpoint
}

type MstCandidate = {
  a: number
  b: number
  distance: number
  keyA: number
  keyB: number
}

function buildMstEdges(
  endpoints: RoutedEndpoint[],
  hub: HubGroupInfo,
  makeEdge: (
    source: string,
    target: string,
    sourceHandle: string | undefined,
    targetHandle: string | undefined
  ) => Edge
): Edge[] {
  if (endpoints.length === 0) {
    return []
  }
  const nodes: MstNode[] = [
    { kind: 'hub', key: 0, x: hub.center.x, y: hub.center.y }
  ]
  endpoints.forEach((endpoint, index) => {
    nodes.push({
      kind: 'endpoint',
      key: index + 1,
      x: endpoint.x,
      y: endpoint.y,
      endpoint
    })
  })

  const candidates: MstCandidate[] = []
  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const nodeA = nodes[i]
      const nodeB = nodes[j]
      const distance = Math.abs(nodeA.x - nodeB.x) + Math.abs(nodeA.y - nodeB.y)
      candidates.push({
        a: i,
        b: j,
        distance,
        keyA: nodeA.key,
        keyB: nodeB.key
      })
    }
  }

  candidates.sort((left, right) => {
    if (left.distance !== right.distance) {
      return left.distance - right.distance
    }
    if (left.keyA !== right.keyA) {
      return left.keyA - right.keyA
    }
    return left.keyB - right.keyB
  })

  const uf = new UnionFind(nodes.length)
  const edges: Edge[] = []
  candidates.forEach((candidate) => {
    if (!uf.union(candidate.a, candidate.b)) {
      return
    }
    const nodeA = nodes[candidate.a]
    const nodeB = nodes[candidate.b]
    if (nodeA.kind === 'hub' || nodeB.kind === 'hub') {
      const endpointNode = nodeA.kind === 'hub' ? nodeB : nodeA
      const endpoint = endpointNode.endpoint
      if (!endpoint) {
        return
      }
      edges.push(
        makeEdge(
          endpoint.instanceId,
          hub.nodeId,
          endpoint.pinId,
          HUB_HANDLE_ID
        )
      )
      return
    }
    const endpointA = nodeA.endpoint
    const endpointB = nodeB.endpoint
    if (!endpointA || !endpointB) {
      return
    }
    const [source, target] =
      endpointA.order <= endpointB.order ? [endpointA, endpointB] : [endpointB, endpointA]
    edges.push(
      makeEdge(
        source.instanceId,
        target.instanceId,
        source.pinId,
        target.pinId
      )
    )
  })
  return edges
}

function buildTrunkEdges(
  endpoints: RoutedEndpoint[],
  hub: HubGroupInfo,
  makeEdge: (
    source: string,
    target: string,
    sourceHandle: string | undefined,
    targetHandle: string | undefined
  ) => Edge,
  makeJunctionNode: (centerX: number, centerY: number) => string
): Edge[] {
  if (endpoints.length === 0) {
    return []
  }
  const horizontal = isHorizontalHubOrient(hub.orient)
  const hubCoord = horizontal ? hub.center.x : hub.center.y
  const fixedCoord = horizontal ? hub.center.y : hub.center.x
  const projectionCoords = endpoints.map((endpoint) =>
    horizontal ? endpoint.x : endpoint.y
  )
  const minCoord = Math.min(hubCoord, ...projectionCoords)
  const maxCoord = Math.max(hubCoord, ...projectionCoords)

  const coordByKey = new Map<number, number>()
  const pushCoord = (value: number) => {
    const key = Math.round(value * 1000)
    if (!coordByKey.has(key)) {
      coordByKey.set(key, value)
    }
  }

  projectionCoords.forEach(pushCoord)
  pushCoord(minCoord)
  pushCoord(maxCoord)
  pushCoord(hubCoord)

  const hubKey = Math.round(hubCoord * 1000)
  const sortedKeys = Array.from(coordByKey.entries()).sort((a, b) => a[0] - b[0])
  const coordToNode = new Map<number, string>()
  sortedKeys.forEach(([key, coord]) => {
    if (key === hubKey) {
      coordToNode.set(key, hub.nodeId)
      return
    }
    const centerX = horizontal ? coord : fixedCoord
    const centerY = horizontal ? fixedCoord : coord
    coordToNode.set(key, makeJunctionNode(centerX, centerY))
  })

  const edges: Edge[] = []
  for (let i = 0; i < sortedKeys.length - 1; i += 1) {
    const fromKey = sortedKeys[i][0]
    const toKey = sortedKeys[i + 1][0]
    const fromNode = coordToNode.get(fromKey)
    const toNode = coordToNode.get(toKey)
    if (!fromNode || !toNode) {
      continue
    }
    const [source, target] = orientTrunkEdge(fromNode, toNode, hub.nodeId)
    edges.push(
      makeEdge(
        source,
        target,
        handleIdForTrunkNode(source, hub.nodeId),
        handleIdForTrunkNode(target, hub.nodeId)
      )
    )
  }

  endpoints.forEach((endpoint) => {
    const projection = horizontal ? endpoint.x : endpoint.y
    const key = Math.round(projection * 1000)
    const targetNode = coordToNode.get(key) ?? hub.nodeId
    edges.push(
      makeEdge(
        endpoint.instanceId,
        targetNode,
        endpoint.pinId,
        handleIdForTrunkNode(targetNode, hub.nodeId)
      )
    )
  })

  return edges
}

function orientTrunkEdge(
  nodeA: string,
  nodeB: string,
  hubNodeId: string
): [string, string] {
  if (nodeA === hubNodeId) {
    return [nodeB, nodeA]
  }
  if (nodeB === hubNodeId) {
    return [nodeA, nodeB]
  }
  return [nodeA, nodeB]
}

function handleIdForTrunkNode(nodeId: string, hubNodeId: string): string {
  return nodeId === hubNodeId ? HUB_HANDLE_ID : JUNCTION_HANDLE_ID
}

function isHorizontalHubOrient(orient: Orient): boolean {
  return orient === 'R0' || orient === 'R180' || orient === 'MX' || orient === 'MY'
}

class UnionFind {
  private parent: number[]
  private rank: number[]

  constructor(size: number) {
    this.parent = Array.from({ length: size }, (_, index) => index)
    this.rank = Array.from({ length: size }, () => 0)
  }

  find(value: number): number {
    if (this.parent[value] !== value) {
      this.parent[value] = this.find(this.parent[value])
    }
    return this.parent[value]
  }

  union(a: number, b: number): boolean {
    const rootA = this.find(a)
    const rootB = this.find(b)
    if (rootA === rootB) {
      return false
    }
    if (this.rank[rootA] < this.rank[rootB]) {
      this.parent[rootA] = rootB
    } else if (this.rank[rootA] > this.rank[rootB]) {
      this.parent[rootB] = rootA
    } else {
      this.parent[rootB] = rootA
      this.rank[rootA] += 1
    }
    return true
  }
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

function normalizeTopology(value: unknown): NetTopology {
  if (value === 'star' || value === 'mst' || value === 'trunk') {
    return value
  }
  return DEFAULT_TOPOLOGY
}

function toPlacementMap(value: unknown): Record<string, Placement> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {}
  }
  const placements: Record<string, Placement> = {}
  for (const [key, placement] of Object.entries(value as Record<string, unknown>)) {
    if (isPlacement(placement)) {
      placements[key] = placement
    }
  }
  return placements
}

function normalizeNetHubEntry(entry: NetHubLayout | undefined): NetHubEntry {
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) {
    return { topology: DEFAULT_TOPOLOGY, hubs: {} }
  }
  const record = entry as Record<string, unknown>
  const hasHubs = Object.prototype.hasOwnProperty.call(record, 'hubs')
  const hasTopology = Object.prototype.hasOwnProperty.call(record, 'topology')
  if (hasHubs || hasTopology) {
    return {
      topology: normalizeTopology(record.topology),
      hubs: toPlacementMap(hasHubs ? record.hubs : {})
    }
  }
  return { topology: DEFAULT_TOPOLOGY, hubs: toPlacementMap(record) }
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

function firstHubPlacement(hubLayout: NetHubLayout | undefined): Placement | undefined {
  const entry = normalizeNetHubEntry(hubLayout)
  return firstHubEntry(entry.hubs)?.placement
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
      const netLabel = netLabelById.get(edge.to) ?? edge.to
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
            <Handle
              id={pin.id}
              type="target"
              position={position}
              style={{ left: pin.x, top: pin.y, transform: 'translate(-50%, -50%)' }}
              className="pin-handle pin-handle--target"
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

function JunctionNodeComponent() {
  return (
    <div className="node junction-node">
      <Handle
        type="source"
        id={JUNCTION_HANDLE_ID}
        position={Position.Top}
        style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
        className="junction-handle"
      />
      <Handle
        type="target"
        id={JUNCTION_HANDLE_ID}
        position={Position.Top}
        style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
        className="junction-handle"
      />
    </div>
  )
}
