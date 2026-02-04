import type { NetTopology, SymbolDefinition } from './types'

export const DEFAULT_GRID_SIZE = 16
export const DEFAULT_TOPOLOGY: NetTopology = 'star'
export const HUB_SIZE = 2
export const HUB_HANDLE_ID = 'hub'
export const JUNCTION_SIZE = 0.6
export const JUNCTION_HANDLE_ID = 'junction'
export const EDGE_STEP_OFFSET_UNITS = 0.8
export const EDGE_STYLE = { stroke: '#e2e8f0', strokeWidth: 2, strokeLinecap: 'round' }
export const PIN_LABEL_INSET_RATIO = 0.6
export const PIN_LABEL_INSET_MIN_PX = 6
export const FALLBACK_SYMBOL: SymbolDefinition = {
  body: { w: 6, h: 4 },
  pins: { left: [] }
}
