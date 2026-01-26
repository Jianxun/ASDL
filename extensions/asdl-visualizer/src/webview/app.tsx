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
const INSTANCE_WIDTH = 6
const INSTANCE_HEIGHT = 4
const HUB_SIZE = 2

type InstanceNodeData = {
  label: string
  orient: string
}

type HubNodeData = {
  label: string
}

type VisualNodeData = InstanceNodeData | HubNodeData

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
        const { x, y } = centerFromNode(node, gridSize, INSTANCE_WIDTH, INSTANCE_HEIGHT)
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
    const pos = topLeftFromCenter(gridX, gridY, gridSize, INSTANCE_WIDTH, INSTANCE_HEIGHT)
    return {
      id: inst.id,
      type: 'instance',
      position: pos,
      data: { label: inst.label, orient: placement?.orient ?? 'R0' },
      style: {
        width: INSTANCE_WIDTH * gridSize,
        height: INSTANCE_HEIGHT * gridSize
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
      const source = edge.from.includes('.') ? edge.from.split('.')[0] : edge.from
      const target = edge.to.includes('.') ? edge.to.split('.')[0] : edge.to
      if (!nodeIds.has(source) || !nodeIds.has(target)) {
        return null
      }
      return {
        id: edge.id,
        source,
        target,
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

function InstanceNodeComponent({ data }: NodeProps<InstanceNodeData>) {
  return (
    <div className="node instance-node">
      <Handle type="target" position={Position.Left} />
      <div className="node-title">{data.label}</div>
      <div className="node-subtitle">{data.orient}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

function HubNodeComponent({ data }: NodeProps<HubNodeData>) {
  return (
    <div className="node hub-node">
      <Handle type="target" position={Position.Left} />
      <div className="hub-dot" />
      <div className="hub-label">{data.label}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}
