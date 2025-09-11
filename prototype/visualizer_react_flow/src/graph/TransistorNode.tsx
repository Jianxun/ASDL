import type { NodeProps } from 'reactflow'
import { Handle, Position } from 'reactflow'
import type { TransistorNodeData } from './types'
import nmosUrl from '../assets/nmos.svg'
import pmosUrl from '../assets/pmos.svg'

export default function TransistorNode({ data, selected }: NodeProps<TransistorNodeData>) {
  const isPmos = data.flavor === 'pmos'

  const drainPos: Position = isPmos ? Position.Bottom : Position.Top
  const sourcePos: Position = isPmos ? Position.Top : Position.Bottom
  const gatePos: Position = Position.Left

  // Use full-size container so it matches React Flow node style width/height
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', boxSizing: 'border-box', border: selected ? '2px solid #2563eb' : '1px solid #9ca3af', borderRadius: 6, background: '#fff' }}>
      {/* External SVG via Vite asset pipeline */}
      <img src={isPmos ? pmosUrl : nmosUrl} alt={isPmos ? 'PMOS' : 'NMOS'} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain', pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', top: 6, left: 8, fontSize: 12, color: '#111827' }}>{data.name}</div>
      <div style={{ position: 'absolute', bottom: 6, left: 8, fontSize: 11, color: '#374151' }}>{data.flavor.toUpperCase()}</div>

      {/* Provide both source and target handles for bidirectional connectivity */}
      <Handle id="D" type="source" position={drainPos} style={{ width: 2, height: 2, opacity: 1 }} />
      <Handle id="D" type="target" position={drainPos} style={{ width: 2, height: 2, opacity: 1 }} />

      <Handle id="G" type="source" position={gatePos} style={{ width: 2, height: 2, opacity: 1 }} />
      <Handle id="G" type="target" position={gatePos} style={{ width: 2, height: 2, opacity: 1 }} />

      <Handle id="S" type="source" position={sourcePos} style={{ width: 2, height: 2, opacity: 1 }} />
      <Handle id="S" type="target" position={sourcePos} style={{ width: 2, height: 2, opacity: 1 }} />
    </div>
  )
}


