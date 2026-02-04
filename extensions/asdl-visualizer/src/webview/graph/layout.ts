import type { Edge, Node } from 'reactflow'
import {
  DEFAULT_TOPOLOGY,
  EDGE_STEP_OFFSET_UNITS,
  EDGE_STYLE,
  FALLBACK_SYMBOL,
  HUB_HANDLE_ID,
  HUB_SIZE,
  JUNCTION_SIZE
} from '../constants'
import type {
  GraphPayload,
  HubGroupInfo,
  HubNodeData,
  LayoutPayload,
  NetHubEntry,
  NetHubInfo,
  NetHubLayout,
  Placement,
  RoutedPin,
  VisualNodeData
} from '../types'
import {
  applyOrientPoint,
  computeOrientData,
  computePinPositions,
  mapPinSide,
  normalizeOrient,
  normalizeSymbolBody,
  topLeftFromCenter,
  topLeftFromGrid
} from './geometry'
import {
  buildMstEdges,
  buildStarEdges,
  buildTrunkEdges,
  collectRoutedEndpoints,
  parseEndpoint,
  splitEndpointsByGroups
} from './routing'

export function buildReactFlowGraph(
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
    } as Node<VisualNodeData>
  })

  const hubs: Array<Node<HubNodeData>> = []
  const hubInfoByNet = new Map<string, NetHubInfo>()
  let hubRowIndex = 0

  graph.netHubs.forEach((hub) => {
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
  const junctionNodes: Array<Node<VisualNodeData>> = []
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
        ...buildStarEdges(
          routable,
          hubGroup,
          makeEdge
        )
      )
    }
  })

  return { nodes: [...instances, ...hubs, ...junctionNodes], edges }
}

export function normalizeNetHubEntry(entry: NetHubLayout | undefined): NetHubEntry {
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

export function firstHubEntry(
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

export function firstHubPlacement(hubLayout: NetHubLayout | undefined): Placement | undefined {
  const entry = normalizeNetHubEntry(hubLayout)
  return firstHubEntry(entry.hubs)?.placement
}

function isPlacement(value: unknown): value is Placement {
  if (!value || typeof value !== 'object') {
    return false
  }
  const candidate = value as Placement
  return Number.isFinite(candidate.x) && Number.isFinite(candidate.y)
}

function normalizeTopology(value: unknown): NetHubEntry['topology'] {
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

function buildNetLabelMap(
  instanceId: string,
  pins: Array<{ id: string; connectByLabel: boolean }>,
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
