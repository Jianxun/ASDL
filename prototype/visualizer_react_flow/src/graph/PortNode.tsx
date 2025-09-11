import type { NodeProps } from 'reactflow'
import { Handle, Position } from 'reactflow'
import type { PortNodeData } from './types'

export default function PortNode({ data, selected }: NodeProps<PortNodeData>) {
  // Visual side: where the dot sits
  const visualPos: Position = data.side === 'left' ? Position.Left : Position.Right
  // Handle direction: inputs should accept from the left (target on left), outputs should send to the right (source on right)
  const isInput = data.direction === 'in'
  const isOutput = data.direction === 'out'

  // For bidir or missing, expose both sides
  const showLeftSource = !isInput
  const showLeftTarget = isInput || data.direction === 'bidir' || !data.direction
  const showRightSource = isOutput || data.direction === 'bidir' || !data.direction
  const showRightTarget = !isOutput

  return (
    <div style={{ position: 'relative', minWidth: 60, height: 18, display: 'flex', alignItems: 'center' }}>
      {data.side === 'right' && (
        <div style={{ marginRight: 6, fontSize: 12, color: '#111827' }}>{data.name}</div>
      )}
      <div
        style={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          background: '#111827',
          border: selected ? '2px solid #2563eb' : '1px solid #111827',
        }}
        title={data.name}
      />
      {data.side === 'left' && (
        <div style={{ marginLeft: 6, fontSize: 12, color: '#111827' }}>{data.name}</div>
      )}

      {/* Handles: place on both sides according to direction policy */}
      {showLeftSource && <Handle id="P" type="source" position={Position.Left} style={{ width: 10, height: 10, opacity: 0 }} />}
      {showLeftTarget && <Handle id="P" type="target" position={Position.Left} style={{ width: 10, height: 10, opacity: 0 }} />}
      {showRightSource && <Handle id="P" type="source" position={Position.Right} style={{ width: 10, height: 10, opacity: 0 }} />}
      {showRightTarget && <Handle id="P" type="target" position={Position.Right} style={{ width: 10, height: 10, opacity: 0 }} />}
    </div>
  )
}


