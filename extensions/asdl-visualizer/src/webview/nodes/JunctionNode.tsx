import React from 'react'
import { Handle, Position } from 'reactflow'
import { JUNCTION_HANDLE_ID } from '../constants'

export function JunctionNodeComponent() {
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
