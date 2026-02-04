import React, { useEffect, useMemo } from 'react'
import { Handle, type NodeProps, useUpdateNodeInternals } from 'reactflow'
import type { InstanceNodeData } from '../types'
import {
  applyOrientPoint,
  computeNetLabelPosition,
  computeOrientData,
  computePinNamePosition,
  mapPinSide,
  normalizeOrient,
  pinLabelInset,
  positionFromSide
} from '../graph/geometry'

export function InstanceNodeComponent({ id, data }: NodeProps<InstanceNodeData>) {
  const updateNodeInternals = useUpdateNodeInternals()
  const orient = normalizeOrient(data.orient)
  const baseWidth = data.body.w * data.gridSize
  const baseHeight = data.body.h * data.gridSize
  const orientData = computeOrientData(baseWidth, baseHeight, orient)

  const orientedPins = useMemo(() => {
    const inset = pinLabelInset(data.gridSize)
    return data.pins.map((pin) => {
      const x = pin.x * data.gridSize
      const y = pin.y * data.gridSize
      const { x: ox, y: oy } = applyOrientPoint(x, y, orientData)
      const side = mapPinSide(pin.side, orientData)
      const nameText = pin.visible ? pin.name : null
      const namePos = nameText ? computePinNamePosition(ox, oy, side, inset) : null
      const netLabelText = data.netLabels[pin.id] ?? null
      const netLabelPos = netLabelText ? computeNetLabelPosition(ox, oy, side, inset) : null
      return { ...pin, x: ox, y: oy, side, nameText, namePos, netLabelText, netLabelPos }
    })
  }, [data.pins, data.gridSize, data.netLabels, orientData])

  useEffect(() => {
    updateNodeInternals(id)
  }, [id, orient, updateNodeInternals])

  const glyph = data.glyph
  const glyphStyle = glyph
    ? {
        left: glyph.box.x * data.gridSize,
        top: glyph.box.y * data.gridSize,
        width: glyph.box.w * data.gridSize,
        height: glyph.box.h * data.gridSize
      }
    : undefined
  return (
    <div className="node instance-node">
      <div
        className="symbol-layer"
        style={{
          width: baseWidth,
          height: baseHeight,
          transformOrigin: '0 0',
          transform: orientData.transform
        }}
      >
        {glyph && (
          <svg
            className="glyph-frame"
            style={glyphStyle}
            viewBox={glyph.viewbox}
            preserveAspectRatio="xMidYMid meet"
          >
            <image
              href={glyph.src}
              width="100%"
              height="100%"
              preserveAspectRatio="xMidYMid meet"
            />
          </svg>
        )}
      </div>
      {orientedPins.map((pin) => {
        const position = positionFromSide(pin.side)
        return (
          <React.Fragment key={`${pin.id}-${pin.side}`}>
            <Handle
              id={pin.id}
              type="source"
              position={position}
              style={{ left: pin.x, top: pin.y, transform: 'translate(-50%, -50%)' }}
              className="pin-handle"
            />
            <Handle
              id={pin.id}
              type="target"
              position={position}
              style={{ left: pin.x, top: pin.y, transform: 'translate(-50%, -50%)' }}
              className="pin-handle pin-handle--target"
            />
            {pin.nameText && pin.namePos && (
              <div
                className={`pin-name pin-name--${pin.side}`}
                style={{ left: pin.namePos.x, top: pin.namePos.y }}
              >
                {pin.nameText}
              </div>
            )}
            {pin.netLabelText && pin.netLabelPos && (
              <div
                className={`net-label net-label--${pin.side}`}
                style={{ left: pin.netLabelPos.x, top: pin.netLabelPos.y }}
              >
                {pin.netLabelText}
              </div>
            )}
          </React.Fragment>
        )
      })}
      <div className="node-title">{data.label}</div>
      <div className="node-subtitle">{data.orient}</div>
    </div>
  )
}
