import React, { useEffect, useMemo, useRef } from 'react'
import ReactFlow, {
  Background,
  ConnectionLineType,
  Controls,
  type NodeTypes,
  type ReactFlowInstance
} from 'reactflow'
import 'reactflow/dist/style.css'

import { EDGE_STEP_OFFSET_UNITS, EDGE_STYLE } from './constants'
import { HubNodeComponent } from './nodes/HubNode'
import { InstanceNodeComponent } from './nodes/InstanceNode'
import { JunctionNodeComponent } from './nodes/JunctionNode'
import { useVisualizerState } from './state/useVisualizerState'

export function App() {
  const {
    graph,
    layout,
    diagnostics,
    gridSize,
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onSave,
    fitViewToken
  } = useVisualizerState()
  const reactFlowRef = useRef<ReactFlowInstance | null>(null)

  const nodeTypes = useMemo<NodeTypes>(() => ({
    instance: InstanceNodeComponent,
    hub: HubNodeComponent,
    junction: JunctionNodeComponent
  }), [])

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
