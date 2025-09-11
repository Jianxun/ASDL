import type { NodeProps } from 'reactflow'
import { Handle, Position } from 'reactflow'
import type { PortNodeData } from './types'

export default function PortNode({ data, selected }: NodeProps<PortNodeData>) {
  // Visual side: where the dot sits (currently used only for label placement)
  const isInput = data.direction === 'in'
  const isOutput = data.direction === 'out'

  // Handle placement policy:
  // - Input: handles on RIGHT only (source+target), so anchors face right
  // - Output: handles on LEFT only (source+target), so anchors face left
  // - Bidir/unspecified: handles on BOTH sides (source+target)
  const showLeft = isOutput || data.direction === 'bidir' || !data.direction
  const showRight = isInput || data.direction === 'bidir' || !data.direction

  // Label placement policy (opposite of wire entry side):
  // - Input (wires from right): label on LEFT
  // - Output (wires from left): label on RIGHT
  // - Bidir/unspecified: label opposite the dot's side to avoid overlap
  const showLabelLeft = isInput || (!isInput && !isOutput && data.side === 'right')
  const showLabelRight = isOutput || (!isInput && !isOutput && data.side === 'left')

  const grid = data.gridSize ?? 16
  // Use a 2×grid node box so the left/right handles sit exactly on grid lines when the center is snapped to grid.
  const size = 2 * grid

  const left_adjust = isInput ? grid : 0

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      {/* Labels positioned opposite to wire entry, absolutely, so they don't affect handle alignment */}
      {showLabelLeft && (
        <div style={{ position: 'absolute', right: size + 2, top: '50%', transform: 'translateY(-50%)', fontSize: 12, color: '#111827', whiteSpace: 'nowrap' }}>{data.name}</div>
      )}
      {showLabelRight && (
        <div style={{ position: 'absolute', left: size + 2, top: '50%', transform: 'translateY(-50%)', fontSize: 12, color: '#111827', whiteSpace: 'nowrap' }}>{data.name}</div>
      )}

      {/* Dot centered inside the node box */}
      <div
        style={{
          position: 'absolute',
          left: left_adjust, // adjust according to the port direction
          top: grid / 2, 
          width: grid,
          height: grid,
          borderRadius: '50%',
          background: '#111827',
          border: selected ? '2px solid #2563eb' : '1px solid #111827',
          boxSizing: 'border-box',
        }}
        title={data.name}
      />

      {/* Handles: placed at node edges so anchors sit directly next to the circle */}
      {showLeft && <Handle id="P" type="source" position={Position.Left} style={{ width: 2, height: 2, opacity: 0 }} />}
      {showLeft && <Handle id="P" type="target" position={Position.Left} style={{ width: 2, height: 2, opacity: 0 }} />}
      {showRight && <Handle id="P" type="source" position={Position.Right} style={{ width: 2, height: 2, opacity: 0 }} />}
      {showRight && <Handle id="P" type="target" position={Position.Right} style={{ width: 2, height: 2, opacity: 0 }} />}
    </div>
  )
}


