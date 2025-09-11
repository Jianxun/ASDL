import 'reactflow/dist/style.css'
import ReactFlow, { Background, Controls, MiniMap, useEdgesState, useNodesState, addEdge, ConnectionLineType } from 'reactflow'
import type { Connection, DefaultEdgeOptions } from 'reactflow'
import { useCallback } from 'react'

const defaultEdgeOptions: DefaultEdgeOptions = { type: 'step' }

export default function App() {
  const [nodes, , onNodesChange] = useNodesState([
    { id: 'a', position: { x: 100, y: 100 }, data: { label: 'A' }, type: 'default' },
    { id: 'b', position: { x: 400, y: 200 }, data: { label: 'B' }, type: 'default' }
  ])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge(connection, eds))
  }, [setEdges])

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
        fitView
        snapToGrid
        snapGrid={[16, 16]}
      >
        <Background gap={16} size={1} />
        <MiniMap />
        <Controls />
      </ReactFlow>
    </div>
  )
}
