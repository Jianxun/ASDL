export type TransistorFlavor = 'nmos' | 'pmos'

export interface TransistorNodeData {
  name: string
  flavor: TransistorFlavor
  w?: string
  l?: string
}

export type PortSide = 'left' | 'right'
export type PortDirection = 'in' | 'out' | 'bidir'

export interface PortNodeData {
  name: string
  side: PortSide
  direction?: PortDirection
}

// JSON graph file schema for import/export
export interface GridPosition {
  gx: number
  gy: number
}

export type VisualizerNodeType = 'transistor' | 'port'

export interface GraphNode<TData = TransistorNodeData | PortNodeData> {
  id: string
  type: VisualizerNodeType
  data: TData
  position: GridPosition
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
  nodes: Array<GraphNode>
  edges?: Array<GraphEdge>
}

export const DEFAULT_GRID_SIZE = 16


