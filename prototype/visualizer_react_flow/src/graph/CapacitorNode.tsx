import type { NodeProps } from 'reactflow'
import { Handle, Position } from 'reactflow'
import type { CapacitorNodeData } from './types'
import capUrl from '../assets/cap.svg'

export default function CapacitorNode({ data, selected }: NodeProps<CapacitorNodeData>) {
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', boxSizing: 'border-box', border: selected ? '2px solid #2563eb' : '1px solid #9ca3af', borderRadius: 6, background: '#fff' }}>
      <img src={capUrl} alt={'CAP'} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain', pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', top: 6, left: 8, fontSize: 12, color: '#111827' }}>{data.name}</div>

      {/* Handles at top middle and bottom middle */}
      <Handle id="PLUS" type="source" position={Position.Top} style={{ width: 2, height: 2, opacity: 1 }} />
      <Handle id="PLUS" type="target" position={Position.Top} style={{ width: 2, height: 2, opacity: 1 }} />

      <Handle id="MINUS" type="source" position={Position.Bottom} style={{ width: 2, height: 2, opacity: 1 }} />
      <Handle id="MINUS" type="target" position={Position.Bottom} style={{ width: 2, height: 2, opacity: 1 }} />
    </div>
  )
}


