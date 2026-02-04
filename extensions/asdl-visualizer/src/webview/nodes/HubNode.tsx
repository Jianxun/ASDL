import React from 'react'
import { Handle, type NodeProps } from 'reactflow'
import { HUB_HANDLE_ID } from '../constants'
import type { HubNodeData } from '../types'
import {
  mapVectorToSide,
  normalizeOrient,
  orientMatrix,
  positionFromSide
} from '../graph/geometry'

export function HubNodeComponent({ data }: NodeProps<HubNodeData>) {
  const orient = normalizeOrient(data.orient)
  const { a, b } = orientMatrix(orient)
  const handlePosition = positionFromSide(mapVectorToSide(a, b))
  return (
    <div className="node hub-node">
      <Handle
        type="target"
        id={HUB_HANDLE_ID}
        position={handlePosition}
        style={{ left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
        className="hub-handle"
      />
      <div className="hub-dot" />
      <div className="hub-label">{data.label}</div>
    </div>
  )
}
