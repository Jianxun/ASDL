import 'reactflow/dist/style.css'
import ReactFlow, { Background, Controls, MiniMap, useEdgesState, useNodesState, addEdge, ConnectionLineType } from 'reactflow'
import type { Connection, DefaultEdgeOptions, Node, Edge, NodeTypes, IsValidConnection } from 'reactflow'
import TransistorNode from './graph/TransistorNode'
import PortNode from './graph/PortNode'
import type { TransistorNodeData, PortNodeData } from './graph/types'
import { useCallback } from 'react'

const defaultEdgeOptions: DefaultEdgeOptions = { type: 'step' }

export default function App() {
  const nodeTypes: NodeTypes = {
    transistor: TransistorNode,
    port: PortNode,
  }

  const initialNodes: Array<Node<TransistorNodeData | PortNodeData>> = [
    { id: 'M1', type: 'transistor', position: { x: 200, y: 160 }, data: { name: 'M1', flavor: 'nmos' } },
    { id: 'M2', type: 'transistor', position: { x: 480, y: 160 }, data: { name: 'M2', flavor: 'pmos' } },
    { id: 'VIN', type: 'port', position: { x: 100, y: 200 }, data: { name: 'vin', side: 'right' } },
    { id: 'VOUT', type: 'port', position: { x: 720, y: 200 }, data: { name: 'vout', side: 'left' } },
  ]

  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState<Array<Edge>>([])

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

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
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
        snapGrid={[16, 16]}
        nodeTypes={nodeTypes}
      >
        <Background gap={16} size={1} />
        <MiniMap />
        <Controls />
      </ReactFlow>
    </div>
  )
}
