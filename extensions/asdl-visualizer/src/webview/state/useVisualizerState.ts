import { useCallback, useEffect, useRef, useState } from 'react'
import {
  applyNodeChanges,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeChange,
  type Viewport
} from 'reactflow'
import { DEFAULT_GRID_SIZE, HUB_SIZE } from '../constants'
import type {
  GraphPayload,
  HubNodeData,
  InstanceNodeData,
  LayoutPayload,
  VisualNodeData,
  WebviewMessage
} from '../types'
import {
  buildReactFlowGraph,
  firstHubEntry,
  normalizeNetHubEntry,
  recomputeRoutingGraph
} from '../graph/layout'
import {
  centerFromNode,
  gridFromTopLeft,
  normalizeOrient
} from '../graph/geometry'

declare function acquireVsCodeApi(): { postMessage: (message: unknown) => void }

const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi() : null

export function useVisualizerState() {
  const [graph, setGraph] = useState<GraphPayload | null>(null)
  const [layout, setLayout] = useState<LayoutPayload | null>(null)
  const [diagnostics, setDiagnostics] = useState<string[]>([])
  const [gridSize, setGridSize] = useState<number>(DEFAULT_GRID_SIZE)
  const [nodes, setNodes] = useNodesState<VisualNodeData>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [fitViewToken, setFitViewToken] = useState(0)
  const [restoreViewportToken, setRestoreViewportToken] = useState(0)
  const [viewportToRestore, setViewportToRestore] = useState<Viewport | null>(null)
  const graphRef = useRef<GraphPayload | null>(null)
  const pendingReloadRef = useRef(false)
  const pendingViewportRef = useRef<Viewport | null>(null)

  useEffect(() => {
    const handleMessage = (event: MessageEvent<WebviewMessage>) => {
      const message = event.data
      if (message.type === 'loadGraph') {
        const forceReload = pendingReloadRef.current
        pendingReloadRef.current = false
        const nextGraph = message.payload.graph
        const prevGraph = graphRef.current
        const isSameModule = prevGraph?.moduleId === nextGraph.moduleId
        const isSameShape =
          prevGraph &&
          prevGraph.instances.length === nextGraph.instances.length &&
          prevGraph.netHubs.length === nextGraph.netHubs.length &&
          prevGraph.edges.length === nextGraph.edges.length
        const shouldRebuild = forceReload || !prevGraph || !isSameModule || !isSameShape

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
          if (pendingViewportRef.current) {
            setViewportToRestore(pendingViewportRef.current)
            setRestoreViewportToken((token) => token + 1)
          } else {
            setFitViewToken((token) => token + 1)
          }
        }
        pendingViewportRef.current = null
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
          moduleLayout.net_hubs[layoutKey] ??
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

  const onReload = useCallback((viewport: Viewport | null) => {
    pendingReloadRef.current = true
    pendingViewportRef.current = viewport
    vscode?.postMessage({
      type: 'reload',
      payload: { moduleId: graphRef.current?.moduleId ?? null }
    })
  }, [])

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      const shouldRecompute = changes.some(
        (change) => change.type === 'position' || change.type === 'dimensions'
      )
      setNodes((prevNodes) => {
        const nextNodes = applyNodeChanges(changes, prevNodes)
        if (!shouldRecompute || !graphRef.current) {
          return nextNodes
        }
        const baseNodes = nextNodes.filter((node) => node.type !== 'junction')
        const { edges: nextEdges, junctionNodes } = recomputeRoutingGraph(
          graphRef.current,
          baseNodes,
          gridSize
        )
        setEdges(nextEdges)
        return [...baseNodes, ...junctionNodes] as Array<Node<VisualNodeData>>
      })
    },
    [gridSize, setEdges, setNodes]
  )

  return {
    graph,
    layout,
    diagnostics,
    gridSize,
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onSave,
    onReload,
    fitViewToken,
    restoreViewportToken,
    viewportToRestore
  }
}
