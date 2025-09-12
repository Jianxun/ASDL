import 'reactflow/dist/style.css'
import ReactFlow, { Background, Controls, MiniMap, useEdgesState, useNodesState, addEdge, ConnectionLineType } from 'reactflow'
import type { Connection, DefaultEdgeOptions, Node, Edge, NodeTypes, IsValidConnection } from 'reactflow'
import TransistorNode from './graph/TransistorNode'
import PortNode from './graph/PortNode'
import InstanceNode from './graph/InstanceNode'
import ResistorNode from './graph/ResistorNode'
import CapacitorNode from './graph/CapacitorNode'
import type { TransistorNodeData, PortNodeData, InstanceNodeData, ResistorNodeData, CapacitorNodeData } from './graph/types'
import { DEFAULT_GRID_SIZE, type GraphEdge, type GraphFile, type GraphNodeV2 } from './graph/types'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

const defaultEdgeOptions: DefaultEdgeOptions = {
  type: 'step',
  style: { stroke: '#111827', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round' },
}

export default function App() {
  const nodeTypes: NodeTypes = {
    transistor: TransistorNode,
    port: PortNode,
    instance: InstanceNode,
    resistor: ResistorNode,
    capacitor: CapacitorNode,
  }

  const [nodes, setNodes, onNodesChange] = useNodesState<TransistorNodeData | PortNodeData | InstanceNodeData | ResistorNodeData | CapacitorNodeData>([])
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

  // Node sizes aligned to grid (multiples of gridSize)
  const TRANSISTOR_W = useMemo(() => 6 * gridSize, [gridSize]) // 8 columns
  const TRANSISTOR_H = useMemo(() => 6 * gridSize, [gridSize]) // 6 rows
  const PORT_SIZE = useMemo(() => 2 * gridSize, [gridSize]) // box is 2 grid to align handles; dot drawn smaller within
  const INSTANCE_W = useMemo(() => 6 * gridSize, [gridSize])
  const INSTANCE_H = useMemo(() => 4 * gridSize, [gridSize])

  // Exact model mapping to primitive symbols
  const PRIMITIVE_MAP = useMemo<Record<string, { symbol: 'nmos'|'pmos'|'resistor'|'capacitor'; pins: string[] }>>(() => ({
    'nmos': { symbol: 'nmos', pins: ['D','G','S'] },
    'pmos': { symbol: 'pmos', pins: ['D','G','S'] },
    'res': { symbol: 'resistor', pins: ['PLUS','MINUS'] },
    'cap': { symbol: 'capacitor', pins: ['PLUS','MINUS'] },
  }), [])

  function classifyNode(n: GraphNodeV2): 'port' | 'transistor' | 'instance' | 'resistor' | 'capacitor' {
    const t: string | undefined = (n as any).type
    if (t === 'port') return 'port'
    if (t === 'transistor') return 'transistor' // legacy files
    if (t === 'instance') {
      const model = (n as any).model as string | undefined
      if (model && PRIMITIVE_MAP[model]) {
        const sym = PRIMITIVE_MAP[model].symbol
        if (sym === 'nmos' || sym === 'pmos') return 'transistor'
        if (sym === 'resistor') return 'resistor'
        if (sym === 'capacitor') return 'capacitor'
      }
      return 'instance'
    }
    // Fallback: if data looks like a port
    if ((n as any).data && (n as any).type === 'port') return 'port'
    return 'instance'
  }

  const toReactFlowNodes = useCallback((gnodes: Array<GraphNodeV2>): Array<Node<TransistorNodeData | PortNodeData | InstanceNodeData | ResistorNodeData | CapacitorNodeData>> => {
    return gnodes.map((n) => {
      const kind = classifyNode(n)
      const width = kind === 'port' ? PORT_SIZE : (kind === 'transistor' || kind === 'resistor' || kind === 'capacitor' ? TRANSISTOR_W : INSTANCE_W)
      const height = kind === 'port' ? PORT_SIZE : (kind === 'transistor' || kind === 'resistor' || kind === 'capacitor' ? TRANSISTOR_H : INSTANCE_H)
      // Interpret gx,gy as CENTER coordinates; convert to top-left for React Flow
      const cx = pixelFromGrid((n as any).position.gx)
      const cy = pixelFromGrid((n as any).position.gy)
      const x = Math.round(cx - width / 2)
      const y = Math.round(cy - height / 2)

      let data: TransistorNodeData | PortNodeData | InstanceNodeData | ResistorNodeData | CapacitorNodeData
      if (kind === 'port') {
        const pdata = (n as any).data ?? {}
        data = { ...(pdata as any), gridSize } as PortNodeData
      } else if (kind === 'transistor') {
        // Legacy transistor or instance mapped to primitive
        if ((n as any).data && (n as any).type === 'transistor') {
          data = { ...((n as any).data as any), gridSize } as TransistorNodeData
        } else {
          const model = (n as any).model as string
          const map = PRIMITIVE_MAP[model]
          const sym = map.symbol
          const flavor: 'nmos'|'pmos' = sym === 'pmos' ? 'pmos' : 'nmos'
          data = { name: (n as any).id, flavor, gridSize }
        }
      } else if (kind === 'resistor') {
        data = { name: (n as any).id, gridSize } as ResistorNodeData
      } else if (kind === 'capacitor') {
        data = { name: (n as any).id, gridSize } as CapacitorNodeData
      } else {
        const pinList = (n as any).pin_list as Record<string, any> | undefined
        const pins = pinList ? Object.keys(pinList) : []
        data = { name: (n as any).id, model: (n as any).model ?? '', pins, gridSize }
      }

      return {
        id: (n as any).id,
        type: kind,
        position: { x, y },
        data,
        style: { width, height },
      }
    })
  }, [gridSize, PORT_SIZE, TRANSISTOR_W, TRANSISTOR_H, INSTANCE_W, INSTANCE_H, PRIMITIVE_MAP])

  const toReactFlowEdges = useCallback((gedges: Array<GraphEdge>): Array<Edge> => {
    return gedges.map((e, idx) => ({
      id: e.id ?? `e${idx}`,
      source: e.source,
      sourceHandle: e.sourceHandle,
      target: e.target,
      targetHandle: e.targetHandle,
      type: 'step',
      style: { stroke: '#111827', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round' },
    }))
  }, [])

  const handleLoadJson = useCallback((g: GraphFile) => {
    const gs = g.gridSize && g.gridSize > 0 ? g.gridSize : DEFAULT_GRID_SIZE
    setGridSize(gs)
    const rfNodes = toReactFlowNodes(g.nodes as any)
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
      nodes: nodes.map((n) => {
        const isPort = n.type === 'port'
        const width = isPort ? PORT_SIZE : TRANSISTOR_W
        const height = isPort ? PORT_SIZE : TRANSISTOR_H
        // Convert from top-left back to CENTER grid units
        const cx = n.position.x + width / 2
        const cy = n.position.y + height / 2
        return {
          id: n.id,
          type: String(n.type) as any,
          data: n.data as any,
          position: { gx: gridFromPixel(cx), gy: gridFromPixel(cy) },
        }
      }),
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
    const params = new URLSearchParams(window.location.search)
    const fname = params.get('file') || 'graph_layout.json'
    a.download = fname
    a.click()
    URL.revokeObjectURL(url)
  }, [nodes, edges, gridSize])

  // Auto-load data from URL (inline base64 JSON) or fall back to public/graph.json
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const params = new URLSearchParams(window.location.search)
        const b64 = params.get('data')
        if (b64) {
          try {
            const decoded = atob(b64)
            const g = JSON.parse(decoded) as GraphFile
            if (!cancelled) handleLoadJson(g)
            return
          } catch (e) {
            // eslint-disable-next-line no-console
            console.error('Failed to parse inline data param:', e)
          }
        }
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
        connectionLineStyle={{ stroke: '#111827', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round' }}
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
