export type TransistorFlavor = 'nmos' | 'pmos'

export interface TransistorNodeData {
  name: string
  flavor: TransistorFlavor
  w?: string
  l?: string
  gridSize?: number
}

export type PortSide = 'left' | 'right'
export type PortDirection = 'in' | 'out' | 'bidir'

export interface PortNodeData {
  name: string
  side: PortSide
  direction?: PortDirection
  gridSize?: number
}

export interface InstanceNodeData {
  name: string
  model: string
  pins?: string[]
  gridSize?: number
}

export interface ResistorNodeData {
  name: string
  gridSize?: number
}

export interface CapacitorNodeData {
  name: string
  gridSize?: number
}

// JSON graph file schema (v2)
export interface GridPosition { gx: number; gy: number }

export interface PinMeta { dir?: PortDirection; type?: string; role?: string }

// Port nodes keep existing shape via React state, but file schema uses GraphNodeV2
export interface GraphNodeV2 {
  id: string
  type?: 'port' | 'instance'
  model?: string
  // For ports, loader constructs from existing data; for instances, required
  pin_list?: Record<string, PinMeta>
  // Position in grid units (center)
  position: GridPosition
  // Backward compat: allow existing data for ports/transistors (ignored for v2)
  data?: any
}

export interface GraphEdge {
  id?: string
  source: string
  sourceHandle?: string
  target: string
  targetHandle?: string
}

export interface GraphFile {
  gridSize?: number
  nodes: Array<GraphNodeV2>
  edges?: Array<GraphEdge>
}

export const DEFAULT_GRID_SIZE = 16


