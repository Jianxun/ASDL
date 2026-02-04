export type InstanceNode = {
  id: string
  label: string
  pins: string[]
  symbolKey: string
  layoutKey?: string
}

export type NetHubNode = {
  id: string
  label: string
  layoutKey?: string
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

export type GraphPayload = {
  moduleId: string
  instances: InstanceNode[]
  netHubs: NetHubNode[]
  edges: Array<{ id: string; from: string; to: string; conn_label?: string }>
  symbols: Record<string, SymbolDefinition>
  schematic_hints?: SchematicHints | null
}

export type SymbolPins = {
  top?: Array<SymbolPin | null>
  bottom?: Array<SymbolPin | null>
  left?: Array<SymbolPin | null>
  right?: Array<SymbolPin | null>
}

export type SymbolPin = {
  name: string
  offset: number
  visible: boolean
  connect_by_label?: boolean
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

export type Placement = {
  x: number
  y: number
  orient?: string
  label?: string
}

export type NetTopology = 'star' | 'mst' | 'trunk'

export type NetHubEntry = {
  topology?: NetTopology
  hubs: Record<string, Placement>
}

export type NetHubLayout = NetHubEntry | Record<string, Placement>

export type LayoutPayload = {
  schema_version: number
  modules: Record<
    string,
    {
      grid_size?: number
      instances: Record<string, Placement>
      net_hubs: Record<string, NetHubLayout>
    }
  >
}

export type LoadGraphMessage = {
  type: 'loadGraph'
  payload: {
    graph: GraphPayload
    layout: LayoutPayload
    diagnostics?: string[]
  }
}

export type DiagnosticsMessage = {
  type: 'diagnostics'
  payload: { items: string[] }
}

export type WebviewMessage = LoadGraphMessage | DiagnosticsMessage

export type InstanceNodeData = {
  label: string
  orient: string
  body: { w: number; h: number }
  pins: PinPosition[]
  netLabels: Record<string, string | null>
  gridSize: number
  glyph?: SymbolGlyph
}

export type HubNodeData = {
  label: string
  orient: string
  netId: string
  hubKey: string
  layoutKey: string
  topology: NetTopology
}

export type JunctionNodeData = {
  kind: 'junction'
}

export type VisualNodeData = InstanceNodeData | HubNodeData | JunctionNodeData

export type PinSide = 'top' | 'bottom' | 'left' | 'right'
export type Orient = 'R0' | 'R90' | 'R180' | 'R270' | 'MX' | 'MY' | 'MXR90' | 'MYR90'

export type PinPosition = {
  id: string
  name: string
  side: PinSide
  x: number
  y: number
  visible: boolean
  connectByLabel: boolean
}

export type RoutedPin = {
  x: number
  y: number
  side: PinSide
  connectByLabel: boolean
}

export type RoutedEndpoint = {
  id: string
  netId: string
  instanceId: string
  pinId: string
  connLabel?: string
  order: number
  x: number
  y: number
  connectByLabel: boolean
}

export type HubGroupInfo = {
  nodeId: string
  hubKey: string
  layoutKey: string
  orient: Orient
  center: { x: number; y: number }
}

export type NetHubInfo = {
  topology: NetTopology
  groups: HubGroupInfo[]
}
