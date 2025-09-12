import type { NodeProps } from 'reactflow'
import { Handle, Position } from 'reactflow'
import type { InstanceNodeData } from './types'

export default function InstanceNode({ data, selected }: NodeProps<InstanceNodeData>) {
  const pins = data.pins ?? []
  const half = Math.ceil(pins.length / 2)
  const leftPins = pins.slice(0, half)
  const rightPins = pins.slice(half)

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', boxSizing: 'border-box', border: selected ? '2px solid #2563eb' : '1px solid #9ca3af', borderRadius: 6, background: '#fff' }}>
      <div style={{ position: 'absolute', top: 6, left: 8, fontSize: 12, color: '#111827' }}>{data.name}</div>
      <div style={{ position: 'absolute', bottom: 6, left: 8, fontSize: 11, color: '#374151' }}>{data.model}</div>

      {leftPins.map((p, i) => (
        <div key={`L-${p}`}>
          <Handle id={p} type="source" position={Position.Left} style={{ top: 18 + i * 14, width: 2, height: 2, opacity: 1 }} />
          <Handle id={p} type="target" position={Position.Left} style={{ top: 18 + i * 14, width: 2, height: 2, opacity: 1 }} />
          <div style={{ position: 'absolute', left: 6, top: 14 + i * 14, fontSize: 10, color: '#111827' }}>{p}</div>
        </div>
      ))}
      {rightPins.map((p, i) => (
        <div key={`R-${p}`}>
          <Handle id={p} type="source" position={Position.Right} style={{ top: 18 + i * 14, width: 2, height: 2, opacity: 1 }} />
          <Handle id={p} type="target" position={Position.Right} style={{ top: 18 + i * 14, width: 2, height: 2, opacity: 1 }} />
          <div style={{ position: 'absolute', right: 6, top: 14 + i * 14, fontSize: 10, color: '#111827' }}>{p}</div>
        </div>
      ))}
    </div>
  )
}


