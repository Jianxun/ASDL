import { Position, type Node } from 'reactflow'
import {
  FALLBACK_SYMBOL,
  PIN_LABEL_INSET_MIN_PX,
  PIN_LABEL_INSET_RATIO
} from '../constants'
import type {
  Orient,
  PinPosition,
  PinSide,
  SymbolDefinition,
  SymbolPin
} from '../types'

export function topLeftFromCenter(
  gridX: number,
  gridY: number,
  gridSize: number,
  widthUnits: number,
  heightUnits: number
) {
  const width = widthUnits * gridSize
  const height = heightUnits * gridSize
  const cx = gridX * gridSize
  const cy = gridY * gridSize
  return {
    x: Math.round(cx - width / 2),
    y: Math.round(cy - height / 2)
  }
}

export function topLeftFromGrid(gridX: number, gridY: number, gridSize: number) {
  return {
    x: gridX * gridSize,
    y: gridY * gridSize
  }
}

export function centerFromNode(
  node: Node,
  gridSize: number,
  widthUnits: number,
  heightUnits: number
) {
  const width = widthUnits * gridSize
  const height = heightUnits * gridSize
  const cx = node.position.x + width / 2
  const cy = node.position.y + height / 2
  return {
    x: Math.round(cx / gridSize),
    y: Math.round(cy / gridSize)
  }
}

export function gridFromTopLeft(node: Node, gridSize: number) {
  return {
    x: Math.round(node.position.x / gridSize),
    y: Math.round(node.position.y / gridSize)
  }
}

export function normalizeSymbolBody(body: { w?: number; h?: number }) {
  const w =
    typeof body.w === 'number' && Number.isFinite(body.w) && body.w > 0
      ? body.w
      : FALLBACK_SYMBOL.body.w
  const h =
    typeof body.h === 'number' && Number.isFinite(body.h) && body.h > 0
      ? body.h
      : FALLBACK_SYMBOL.body.h
  return { w, h }
}

export function computePinPositions(symbol: SymbolDefinition, body: { w: number; h: number }) {
  const pins: PinPosition[] = []
  const pinConfig = symbol.pins ?? {}

  const pushPins = (
    side: PinSide,
    entries: Array<SymbolPin | null> | undefined,
    edge: number
  ) => {
    if (!entries || entries.length === 0) {
      return
    }
    const span = entries.length > 1 ? entries.length - 1 : 0
    const start = Math.floor((edge - span) / 2)
    entries.forEach((entry, index) => {
      if (!entry) {
        return
      }
      const along = start + index + entry.offset
      const position =
        side === 'left'
          ? { x: 0, y: along }
          : side === 'right'
            ? { x: body.w, y: along }
            : side === 'top'
              ? { x: along, y: 0 }
              : { x: along, y: body.h }
      pins.push({
        id: entry.name,
        name: entry.name,
        side,
        visible: entry.visible,
        connectByLabel: entry.connect_by_label === true,
        ...position
      })
    })
  }

  pushPins('left', pinConfig.left, body.h)
  pushPins('right', pinConfig.right, body.h)
  pushPins('top', pinConfig.top, body.w)
  pushPins('bottom', pinConfig.bottom, body.w)

  return pins
}

export function normalizeOrient(value: string | undefined): Orient {
  const raw = (value ?? 'R0').toUpperCase()
  if (
    raw === 'R0' ||
    raw === 'R90' ||
    raw === 'R180' ||
    raw === 'R270' ||
    raw === 'MX' ||
    raw === 'MY' ||
    raw === 'MXR90' ||
    raw === 'MYR90'
  ) {
    return raw as Orient
  }
  return 'R0'
}

export type OrientMatrix = { a: number; b: number; c: number; d: number }
export type OrientData = OrientMatrix & {
  tx: number
  ty: number
  width: number
  height: number
  transform: string
}

export function orientMatrix(orient: Orient): OrientMatrix {
  const mirrorX = orient.startsWith('MX')
  const mirrorY = orient.startsWith('MY')
  const rotation = orient.endsWith('R90')
    ? 90
    : orient.endsWith('R180')
      ? 180
      : orient.endsWith('R270')
        ? 270
        : 0
  const sx = mirrorY ? -1 : 1
  const sy = mirrorX ? -1 : 1

  const r =
    rotation === 90
      ? { r11: 0, r12: 1, r21: -1, r22: 0 }
      : rotation === 180
        ? { r11: -1, r12: 0, r21: 0, r22: -1 }
        : rotation === 270
          ? { r11: 0, r12: -1, r21: 1, r22: 0 }
          : { r11: 1, r12: 0, r21: 0, r22: 1 }

  return {
    a: r.r11 * sx,
    b: r.r21 * sx,
    c: r.r12 * sy,
    d: r.r22 * sy
  }
}

export function computeOrientData(w: number, h: number, orient: Orient): OrientData {
  const { a, b, c, d } = orientMatrix(orient)
  const points = [
    { x: 0, y: 0 },
    { x: w, y: 0 },
    { x: 0, y: h },
    { x: w, y: h }
  ].map((p) => ({ x: a * p.x + c * p.y, y: b * p.x + d * p.y }))
  const xs = points.map((p) => p.x)
  const ys = points.map((p) => p.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const tx = -minX
  const ty = -minY
  return {
    a,
    b,
    c,
    d,
    tx,
    ty,
    width: maxX - minX,
    height: maxY - minY,
    transform: `matrix(${a}, ${b}, ${c}, ${d}, ${tx}, ${ty})`
  }
}

export function applyOrientPoint(
  x: number,
  y: number,
  orient: OrientData
): { x: number; y: number } {
  return { x: orient.a * x + orient.c * y + orient.tx, y: orient.b * x + orient.d * y + orient.ty }
}

export function mapPinSide(side: PinSide, orient: OrientData): PinSide {
  const vector =
    side === 'left'
      ? { x: -1, y: 0 }
      : side === 'right'
        ? { x: 1, y: 0 }
        : side === 'top'
          ? { x: 0, y: -1 }
          : { x: 0, y: 1 }
  const x = orient.a * vector.x + orient.c * vector.y
  const y = orient.b * vector.x + orient.d * vector.y
  if (Math.abs(x) >= Math.abs(y)) {
    return x < 0 ? 'left' : 'right'
  }
  return y < 0 ? 'top' : 'bottom'
}

export function mapVectorToSide(x: number, y: number): PinSide {
  if (Math.abs(x) >= Math.abs(y)) {
    return x < 0 ? 'left' : 'right'
  }
  return y < 0 ? 'top' : 'bottom'
}

export function positionFromSide(side: PinSide): Position {
  return side === 'left'
    ? Position.Left
    : side === 'right'
      ? Position.Right
      : side === 'top'
        ? Position.Top
        : Position.Bottom
}

export function pinLabelInset(gridSize: number): number {
  return Math.max(PIN_LABEL_INSET_MIN_PX, Math.round(gridSize * PIN_LABEL_INSET_RATIO))
}

export function computePinNamePosition(
  x: number,
  y: number,
  side: PinSide,
  inset: number
): { x: number; y: number } {
  if (side === 'left') {
    return { x: x + inset, y }
  }
  if (side === 'right') {
    return { x: x - inset, y }
  }
  if (side === 'top') {
    return { x, y: y + inset }
  }
  return { x, y: y - inset }
}

export function computeNetLabelPosition(
  x: number,
  y: number,
  side: PinSide,
  inset: number
): { x: number; y: number } {
  if (side === 'left') {
    return { x: x - inset, y }
  }
  if (side === 'right') {
    return { x: x + inset, y }
  }
  if (side === 'top') {
    return { x, y: y - inset }
  }
  return { x, y: y + inset }
}
