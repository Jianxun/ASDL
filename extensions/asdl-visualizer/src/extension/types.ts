export type VisualizerModule = {
  module_id: string
  name: string
  file_id: string
  ports?: string[]
}

export type VisualizerDevice = {
  device_id: string
  name: string
  file_id: string
  ports?: string[]
}

export type VisualizerDump = {
  schema_version: number
  module: VisualizerModule
  instances: Array<{
    inst_id: string
    name_expr_id: string
    ref_kind: 'module' | 'device'
    ref_id: string
    ref_raw?: string
  }>
  nets: Array<{
    net_id: string
    name_expr_id: string
    endpoint_ids?: string[]
  }>
  endpoints: Array<{
    endpoint_id: string
    net_id: string
    port_expr_id: string
    conn_label?: string
  }>
  registries?: {
    pattern_expressions?: Record<string, { raw?: string }> | null
    schematic_hints?: SchematicHints | null
  }
  refs?: {
    modules?: VisualizerModule[]
    devices?: VisualizerDevice[]
  }
}

export type SymbolPin = {
  name: string
  offset: number
  visible: boolean
  connect_by_label?: boolean
}

export type SymbolPins = {
  top?: Array<SymbolPin | null>
  bottom?: Array<SymbolPin | null>
  left?: Array<SymbolPin | null>
  right?: Array<SymbolPin | null>
}

export type SymbolGlyph = {
  src: string
  viewbox?: string
  box: { x: number; y: number; w: number; h: number }
}

export type SymbolDefinition = {
  body: { w: number; h: number }
  pins: SymbolPins
  glyph?: SymbolGlyph
}

export type SymbolSidecar = {
  schema_version: number
  modules: Record<string, SymbolDefinition>
  devices?: Record<string, SymbolDefinition>
}

export type VisualizerModuleList = {
  schema_version: number
  modules: VisualizerModule[]
}

export type GraphPayload = {
  moduleId: string
  instances: Array<{
    id: string
    label: string
    pins: string[]
    symbolKey: string
    layoutKey?: string
  }>
  netHubs: Array<{ id: string; label: string; layoutKey?: string }>
  edges: Array<{ id: string; from: string; to: string; conn_label?: string }>
  symbols: Record<string, SymbolDefinition>
  schematic_hints?: SchematicHints | null
}

export type GroupSlice = {
  start: number
  count: number
  label?: string | null
}

export type SchematicHints = {
  net_groups: Record<string, GroupSlice[]>
  hub_group_index: number
}

export type NetTopology = 'star' | 'mst' | 'trunk'

export type HubPlacement = {
  x: number
  y: number
  orient?: string
  label?: string
}

export type NetHubEntry = {
  topology?: NetTopology
  hubs: Record<string, HubPlacement>
}

export type LayoutPayload = {
  schema_version: number
  modules: Record<
    string,
    {
      grid_size?: number
      instances: Record<string, HubPlacement>
      net_hubs: Record<string, NetHubEntry>
    }
  >
}

export type LoadGraphPayload = {
  graph: GraphPayload
  layout: LayoutPayload
  diagnostics: string[]
}
