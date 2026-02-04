import type { Edge } from 'reactflow'
import { HUB_HANDLE_ID, JUNCTION_HANDLE_ID } from '../constants'
import type {
  GroupSlice,
  HubGroupInfo,
  Orient,
  RoutedEndpoint,
  RoutedPin
} from '../types'

export function parseEndpoint(value: string): { nodeId: string; handleId?: string } {
  const splitIndex = value.lastIndexOf('.')
  if (splitIndex > 0 && splitIndex < value.length - 1) {
    return { nodeId: value.slice(0, splitIndex), handleId: value.slice(splitIndex + 1) }
  }
  return { nodeId: value }
}

export function collectRoutedEndpoints(
  edges: Array<{ id: string; from: string; to: string; conn_label?: string }>,
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

export function splitEndpointsByGroups(
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

export function buildMstEdges(
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

export function buildTrunkEdges(
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

export function buildStarEdges(
  endpoints: RoutedEndpoint[],
  hub: HubGroupInfo,
  makeEdge: (
    source: string,
    target: string,
    sourceHandle: string | undefined,
    targetHandle: string | undefined
  ) => Edge
): Edge[] {
  return endpoints.map((endpoint) =>
    makeEdge(
      endpoint.instanceId,
      hub.nodeId,
      endpoint.pinId,
      HUB_HANDLE_ID
    )
  )
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
