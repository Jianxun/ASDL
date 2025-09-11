import type { NodeProps } from 'reactflow'
import { Handle, Position } from 'reactflow'
import type { PortNodeData } from './types'

export default function PortNode({ data, selected }: NodeProps<PortNodeData>) {
  const position: Position = data.side === 'left' ? Position.Left : Position.Right
  return (
    <div style={{ position: 'relative', width: 14, height: 14 }}>
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
      <Handle id="P" type="target" position={position} style={{ width: 10, height: 10, opacity: 0 }} />
    </div>
  )
}


