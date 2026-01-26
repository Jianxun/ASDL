import type { GraphPayload, VisualizerDump } from './types'

export function buildGraphFromDump(
  dump: VisualizerDump,
  diagnostics: string[]
): GraphPayload {
  const patternExpressions = dump.registries?.pattern_expressions ?? {}
  const devices = new Map(
    (dump.refs?.devices ?? []).map((device) => [device.device_id, device])
  )
  const modules = new Map(
    (dump.refs?.modules ?? []).map((module) => [module.module_id, module])
  )

  const resolveExprRaw = (exprId: string | undefined) => {
    if (!exprId) {
      return ''
    }
    const raw = patternExpressions[exprId]?.raw
    return typeof raw === 'string' && raw.length > 0 ? raw : exprId
  }

  const instNameToId = new Map<string, string>()
  const instances =
    dump.instances?.map((inst) => {
      const label = resolveExprRaw(inst.name_expr_id) || inst.ref_raw || inst.inst_id
      if (label) {
        instNameToId.set(label, inst.inst_id)
      }
      const refTarget =
        inst.ref_kind === 'device' ? devices.get(inst.ref_id) : modules.get(inst.ref_id)
      const pins = refTarget?.ports ?? []
      if (!refTarget) {
        diagnostics.push(`Missing ${inst.ref_kind} reference for instance ${label}.`)
      }
      return {
        id: inst.inst_id,
        label,
        pins
      }
    }) ?? []

  const netHubs =
    dump.nets?.map((net) => ({
      id: net.net_id,
      label: resolveExprRaw(net.name_expr_id) || net.net_id
    })) ?? []

  const edges =
    dump.endpoints?.map((endpoint) => {
      const portRaw = resolveExprRaw(endpoint.port_expr_id) || endpoint.port_expr_id
      let from = portRaw
      const splitIndex = portRaw.lastIndexOf('.')
      if (splitIndex > 0 && splitIndex < portRaw.length - 1) {
        const instName = portRaw.slice(0, splitIndex)
        const pinName = portRaw.slice(splitIndex + 1)
        const instId = instNameToId.get(instName)
        if (instId) {
          from = `${instId}.${pinName}`
        }
      }
      return {
        id: endpoint.endpoint_id,
        from,
        to: endpoint.net_id
      }
    }) ?? []

  return {
    moduleId: dump.module.name,
    instances,
    netHubs,
    edges
  }
}

export function buildMockGraph(): GraphPayload {
  return {
    moduleId: 'mock_top',
    instances: [
      { id: 'MN1', label: 'MN1', pins: ['D', 'G', 'S', 'B'] },
      { id: 'MP1', label: 'MP1', pins: ['D', 'G', 'S', 'B'] },
      { id: 'XBUF', label: 'XBUF', pins: ['IN', 'OUT'] }
    ],
    netHubs: [
      { id: 'net_vdd', label: 'VDD' },
      { id: 'net_vss', label: 'VSS' },
      { id: 'net_out', label: 'OUT' }
    ],
    edges: [
      { id: 'e1', from: 'MN1.D', to: 'net_out' },
      { id: 'e2', from: 'MP1.D', to: 'net_out' },
      { id: 'e3', from: 'XBUF.OUT', to: 'net_out' },
      { id: 'e4', from: 'MN1.S', to: 'net_vss' },
      { id: 'e5', from: 'MP1.S', to: 'net_vdd' }
    ]
  }
}
