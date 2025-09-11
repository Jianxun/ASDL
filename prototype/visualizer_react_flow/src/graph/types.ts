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


