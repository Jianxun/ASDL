type GraphPayload = {
  moduleId: string
  instances: Array<{ id: string; label: string; pins: string[]; symbolKey: string; layoutKey?: string }>
  netHubs: Array<{ id: string; label: string; layoutKey?: string }>
  edges: Array<{ id: string; from: string; to: string; conn_label?: string }>
  symbols: Record<string, SymbolDefinition>
  schematic_hints?: SchematicHints | null
}

type LayoutPayload = {
  schema_version: number
  modules: Record<
    string,
    {
      grid_size?: number
      instances: Record<string, { x: number; y: number; orient?: string; label?: string }>
      net_hubs: Record<string, NetHubLayout>
    }
  >
}

type NetTopology = 'star' | 'mst' | 'trunk'

type GroupSlice = {
  start: number
  count: number
  label?: string | null
}

type SchematicHints = {
  net_groups: Record<string, GroupSlice[]>
  hub_group_index: number
}

type NetHubEntry = {
  topology?: NetTopology
  hubs: Record<string, { x: number; y: number; orient?: string; label?: string }>
}

type NetHubLayout = NetHubEntry | Record<string, { x: number; y: number; orient?: string; label?: string }>

type SymbolDefinition = {
  body: { w: number; h: number }
  pins: {
    top?: Array<{ name: string; offset: number; visible: boolean; connect_by_label?: boolean } | null>
    bottom?: Array<{ name: string; offset: number; visible: boolean; connect_by_label?: boolean } | null>
    left?: Array<{ name: string; offset: number; visible: boolean; connect_by_label?: boolean } | null>
    right?: Array<{ name: string; offset: number; visible: boolean; connect_by_label?: boolean } | null>
  }
  glyph?: {
    src: string
    viewbox?: string
    box: { x: number; y: number; w: number; h: number }
  }
}

type LoadGraphMessage = {
  type: 'loadGraph'
  payload: {
    graph: GraphPayload
    layout: LayoutPayload
    diagnostics?: string[]
  }
}

type DiagnosticsMessage = {
  type: 'diagnostics'
  payload: { items: string[] }
}

const DEV_FLAG = 'dev'
const DEV_STARTED_KEY = '__asdl_dev_harness_started__'

export function maybeStartDevHarness() {
  const hasVsCodeApi = typeof (window as unknown as { acquireVsCodeApi?: unknown })
    .acquireVsCodeApi === 'function'
  if (hasVsCodeApi) {
    return
  }

  const params = new URLSearchParams(window.location.search)
  if (!params.has(DEV_FLAG)) {
    return
  }

  const marker = window as unknown as Record<string, boolean>
  if (marker[DEV_STARTED_KEY]) {
    return
  }
  marker[DEV_STARTED_KEY] = true

  loadPayload(params).then((payload) => {
    const loadMessage: LoadGraphMessage = {
      type: 'loadGraph',
      payload: { ...payload, diagnostics: [] }
    }
    const diagMessage: DiagnosticsMessage = {
      type: 'diagnostics',
      payload: { items: [] }
    }
    const attempts = 10
    const intervalMs = 150
    let sent = 0
    const send = () => {
      window.postMessage(loadMessage, '*')
      window.postMessage(diagMessage, '*')
      sent += 1
      if (sent < attempts) {
        window.setTimeout(send, intervalMs)
      }
    }
    window.setTimeout(send, intervalMs)
  })
}

function buildDevPayload(): { graph: GraphPayload; layout: LayoutPayload } {
  const symbolKey = 'mock::device::nfet'
  const moduleKey = 'mock::module::buf'
  const glyphSvg = encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">` +
      `<g stroke="#e2e8f0" stroke-width="6" fill="none" stroke-linecap="round">` +
      `<line x1="25" y1="10" x2="25" y2="90"/>` +
      `<line x1="25" y1="50" x2="65" y2="50"/>` +
      `<line x1="65" y1="20" x2="65" y2="80"/>` +
      `</g>` +
      `</svg>`
  )
  const glyphSrc = `data:image/svg+xml,${glyphSvg}`
  const graph: GraphPayload = {
    moduleId: 'mock_top',
    instances: [
      { id: 'M1', label: 'M1', pins: ['D', 'G', 'S'], symbolKey, layoutKey: 'M1' },
      { id: 'M2', label: 'M2', pins: ['D', 'G', 'S'], symbolKey, layoutKey: 'M2' },
      { id: 'M3', label: 'M3', pins: ['D', 'G', 'S'], symbolKey, layoutKey: 'M3' },
      { id: 'XBUF', label: 'XBUF', pins: ['IN', 'OUT'], symbolKey: moduleKey, layoutKey: 'XBUF' },
      { id: 'XBUF2', label: 'XBUF2', pins: ['IN', 'OUT'], symbolKey: moduleKey, layoutKey: 'XBUF2' }
    ],
    netHubs: [
      { id: 'net_in', label: 'IN', layoutKey: 'IN' },
      { id: 'net_mst', label: 'MID', layoutKey: 'MID' },
      { id: 'net_trunk', label: 'BUS', layoutKey: 'BUS' }
    ],
    edges: [
      { id: 'e1', from: 'M1.G', to: 'net_in', conn_label: '<3>' },
      { id: 'e2', from: 'XBUF.IN', to: 'net_in' },
      { id: 'e3', from: 'M1.D', to: 'net_mst' },
      { id: 'e4', from: 'M2.D', to: 'net_mst' },
      { id: 'e5', from: 'XBUF.OUT', to: 'net_mst' },
      { id: 'e6', from: 'XBUF2.IN', to: 'net_mst', conn_label: '<2>' },
      { id: 'e7', from: 'M2.S', to: 'net_trunk' },
      { id: 'e8', from: 'M3.S', to: 'net_trunk' },
      { id: 'e9', from: 'XBUF2.OUT', to: 'net_trunk' },
      { id: 'e10', from: 'M1.S', to: 'net_trunk' }
    ],
    symbols: {
      [symbolKey]: {
        body: { w: 6, h: 4 },
        pins: {
          left: [
            { name: 'G', offset: 0, visible: true }
          ],
          right: [
            { name: 'D', offset: 0, visible: true },
            { name: 'S', offset: 0, visible: true }
          ]
        },
        glyph: {
          src: glyphSrc,
          viewbox: '0 0 100 100',
          box: { x: 1, y: 0.5, w: 4, h: 3 }
        }
      },
      [moduleKey]: {
        body: { w: 8, h: 4 },
        pins: {
          left: [{ name: 'IN', offset: 0, visible: true, connect_by_label: true }],
          right: [{ name: 'OUT', offset: 0, visible: true }]
        }
      }
    },
    schematic_hints: {
      net_groups: {
        net_trunk: [
          { start: 0, count: 2, label: 'A' },
          { start: 2, count: 2, label: 'B' }
        ]
      },
      hub_group_index: 0
    }
  }

  const layout: LayoutPayload = {
    schema_version: 0,
    modules: {
      mock_top: {
        grid_size: 20,
        instances: {
          M1: { x: 2, y: 2, orient: 'R0' },
          M2: { x: 2, y: 6, orient: 'R0' },
          M3: { x: 18, y: 10, orient: 'R0' },
          XBUF: { x: 10, y: 2, orient: 'R0' },
          XBUF2: { x: 10, y: 14, orient: 'R0' }
        },
        net_hubs: {
          IN: { topology: 'star', hubs: { hub1: { x: 6, y: 2 } } },
          MID: { topology: 'mst', hubs: { hub1: { x: 6, y: 6 } } },
          BUS: {
            topology: 'trunk',
            hubs: {
              hub1: { x: 14, y: 4, orient: 'R0' },
              hub2: { x: 14, y: 10, orient: 'R90' }
            }
          }
        }
      }
    }
  }

  return { graph, layout }
}

async function loadPayload(
  params: URLSearchParams
): Promise<{ graph: GraphPayload; layout: LayoutPayload }> {
  const payloadParam = params.get('payload')
  const candidate = payloadParam || '/dev_payload.json'
  try {
    const response = await fetch(candidate, { cache: 'no-store' })
    if (!response.ok) {
      return buildDevPayload()
    }
    const payload = (await response.json()) as { graph?: GraphPayload; layout?: LayoutPayload }
    if (!payload?.graph || !payload?.layout) {
      return buildDevPayload()
    }
    return { graph: payload.graph, layout: payload.layout }
  } catch {
    return buildDevPayload()
  }
}
