import type { NodeProps } from 'reactflow'
import { Handle, Position } from 'reactflow'
import type { TransistorNodeData } from './types'

function EdgeTick({ x, y, width, height }: { x: number; y: number; width: number; height: number }) {
  return <rect x={x} y={y} width={width} height={height} fill="#111827" rx={1} ry={1} />
}

export default function TransistorNode({ data, selected }: NodeProps<TransistorNodeData>) {
  const isPmos = data.flavor === 'pmos'

  const drainPos: Position = isPmos ? Position.Bottom : Position.Top
  const sourcePos: Position = isPmos ? Position.Top : Position.Bottom
  const gatePos: Position = Position.Left

  return (
    <div style={{ position: 'relative', width: 120, height: 100, border: selected ? '2px solid #2563eb' : '1px solid #9ca3af', borderRadius: 6, background: '#fff' }}>
      <svg width="120" height="100" style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        <EdgeTick x={58} y={2} width={4} height={8} />
        <EdgeTick x={58} y={90} width={4} height={8} />
        <EdgeTick x={2} y={48} width={8} height={4} />
      </svg>
      <div style={{ position: 'absolute', top: 6, left: 8, fontSize: 12, color: '#111827' }}>{data.name}</div>
      <div style={{ position: 'absolute', bottom: 6, left: 8, fontSize: 11, color: '#374151' }}>{data.flavor.toUpperCase()}</div>

      {/* Provide both source and target handles for bidirectional connectivity */}
      <Handle id="D" type="source" position={drainPos} style={{ width: 1, height: 1, opacity: 0 }} />
      <Handle id="D" type="target" position={drainPos} style={{ width: 1, height: 1, opacity: 0 }} />

      <Handle id="G" type="source" position={gatePos} style={{ width: 1, height: 1, opacity: 0 }} />
      <Handle id="G" type="target" position={gatePos} style={{ width: 1, height: 1, opacity: 0 }} />

      <Handle id="S" type="source" position={sourcePos} style={{ width: 1, height: 1, opacity: 0 }} />
      <Handle id="S" type="target" position={sourcePos} style={{ width: 1, height: 1, opacity: 0 }} />
    </div>
  )
}


