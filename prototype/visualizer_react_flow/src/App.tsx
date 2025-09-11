import 'reactflow/dist/style.css'
import ReactFlow, { Background, Controls, MiniMap, useEdgesState, useNodesState, addEdge, ConnectionLineType } from 'reactflow'
import type { Connection, DefaultEdgeOptions, Node, Edge, NodeTypes, IsValidConnection } from 'reactflow'
import TransistorNode from './graph/TransistorNode'
import PortNode from './graph/PortNode'
import type { TransistorNodeData, PortNodeData } from './graph/types'
import { DEFAULT_GRID_SIZE, type GraphEdge, type GraphFile, type GraphNode } from './graph/types'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

const defaultEdgeOptions: DefaultEdgeOptions = { type: 'step' }

export default function App() {
  const nodeTypes: NodeTypes = {
    transistor: TransistorNode,
    port: PortNode,
  }

  const [nodes, setNodes, onNodesChange] = useNodesState<TransistorNodeData | PortNodeData>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Array<Edge>>([])
  const [gridSize, setGridSize] = useState<number>(DEFAULT_GRID_SIZE)
  const rfGrid = useMemo<[number, number]>(() => [gridSize, gridSize], [gridSize])
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge(connection, eds))
  }, [setEdges])

  const isValidConnection: IsValidConnection = useCallback((c) => {
    // Allow same-node connections if handles differ (e.g., diode-connected D-G)
    if (c.source && c.target && c.source === c.target) {
      return c.sourceHandle !== c.targetHandle
    }
    return true
  }, [])

  function pixelFromGrid(g: number): number {
    return g * gridSize
  }

  function gridFromPixel(p: number): number {
    return Math.round(p / gridSize)
  }

  const toReactFlowNodes = useCallback((gnodes: Array<GraphNode>): Array<Node<TransistorNodeData | PortNodeData>> => {
    return gnodes.map((n) => ({
      id: n.id,
      type: n.type,
      position: { x: pixelFromGrid(n.position.gx), y: pixelFromGrid(n.position.gy) },
      data: n.data as TransistorNodeData | PortNodeData,
    }))
  }, [gridSize])

  const toReactFlowEdges = useCallback((gedges: Array<GraphEdge>): Array<Edge> => {
    return gedges.map((e, idx) => ({
      id: e.id ?? `e${idx}`,
      source: e.source,
      sourceHandle: e.sourceHandle,
      target: e.target,
      targetHandle: e.targetHandle,
      type: 'step',
    }))
  }, [])

  const handleLoadJson = useCallback((g: GraphFile) => {
    const gs = g.gridSize && g.gridSize > 0 ? g.gridSize : DEFAULT_GRID_SIZE
    setGridSize(gs)
    const rfNodes = toReactFlowNodes(g.nodes)
    const rfEdges = g.edges ? toReactFlowEdges(g.edges) : []
    setNodes(rfNodes)
    setEdges(rfEdges)
  }, [setNodes, setEdges, toReactFlowNodes, toReactFlowEdges])

  const onSelectFile = useCallback((ev: React.ChangeEvent<HTMLInputElement>) => {
    const file = ev.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result)) as GraphFile
        handleLoadJson(parsed)
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('Failed to parse JSON graph:', err)
      }
    }
    reader.readAsText(file)
  }, [handleLoadJson])

  const triggerOpenFile = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleSaveJson = useCallback(() => {
    const exported: GraphFile = {
      gridSize,
      nodes: nodes.map((n) => ({
        id: n.id,
        type: String(n.type) as any,
        data: n.data as any,
        position: { gx: gridFromPixel(n.position.x), gy: gridFromPixel(n.position.y) },
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        sourceHandle: e.sourceHandle ?? undefined,
        target: e.target,
        targetHandle: e.targetHandle ?? undefined,
      })),
    }
    const blob = new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'graph_layout.json'
    a.click()
    URL.revokeObjectURL(url)
  }, [nodes, edges, gridSize])

  // Auto-load graph.json from public on startup (best-effort)
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const resp = await fetch('/graph.json', { cache: 'no-store' })
        if (!resp.ok) return
        const g = (await resp.json()) as GraphFile
        if (!cancelled) handleLoadJson(g)
      } catch {
        // ignore if not found
      }
    })()
    return () => {
      cancelled = true
    }
  }, [handleLoadJson])

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <div style={{ position: 'absolute', zIndex: 10, top: 8, left: 8, display: 'flex', gap: 8 }}>
        <button onClick={triggerOpenFile}>Load JSON</button>
        <button onClick={handleSaveJson}>Save Layout</button>
        <input ref={fileInputRef} type="file" accept="application/json" onChange={onSelectFile} style={{ display: 'none' }} />
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        defaultEdgeOptions={defaultEdgeOptions}
        connectionLineType={ConnectionLineType.Step}
        isValidConnection={isValidConnection}
        fitView
        snapToGrid
        snapGrid={rfGrid}
        nodeTypes={nodeTypes}
      >
        <Background gap={gridSize} size={1} />
        <MiniMap />
        <Controls />
      </ReactFlow>
    </div>
  )
}
