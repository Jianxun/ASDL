import path from 'path'
import * as vscode from 'vscode'
import YAML from 'yaml'

import { fileExists } from './util'
import type {
  GraphPayload,
  SymbolDefinition,
  SymbolPins,
  SymbolSidecar,
  VisualizerDump
} from './types'

const DEFAULT_SYMBOL_BODY = { w: 6, h: 4 }
const PIN_SIDES = ['top', 'bottom', 'left', 'right'] as const

type PinSide = (typeof PIN_SIDES)[number]

type SymbolLibrary = {
  symbols: Record<string, SymbolDefinition>
  diagnostics: string[]
}

export async function loadSymbolLibrary(
  dump: VisualizerDump
): Promise<SymbolLibrary> {
  const diagnostics: string[] = []
  const symbols: Record<string, SymbolDefinition> = {}

  const fileIds = collectFileIds(dump)
  for (const fileId of fileIds) {
    if (!fileId) {
      continue
    }
    const symbolUri = resolveSymbolSidecarUri(fileId)
    if (!(await fileExists(symbolUri))) {
      diagnostics.push(`Missing symbol sidecar: ${symbolUri.fsPath}`)
      continue
    }
    const raw = await vscode.workspace.fs.readFile(symbolUri)
    const text = Buffer.from(raw).toString('utf8')
    let payload: SymbolSidecar | null = null
    try {
      payload = YAML.parse(text) as SymbolSidecar
    } catch {
      diagnostics.push(`Failed to parse symbol sidecar: ${symbolUri.fsPath}`)
      continue
    }
    if (!payload || typeof payload !== 'object') {
      diagnostics.push(`Invalid symbol sidecar payload: ${symbolUri.fsPath}`)
      continue
    }

    const modules = payload.modules ?? {}
    const devices = payload.devices ?? {}
    for (const [name, rawSymbol] of Object.entries(modules)) {
      const symbol = normalizeSymbolDefinition(
        rawSymbol,
        diagnostics,
        `${symbolUri.fsPath}#modules.${name}`
      )
      symbols[makeSymbolKey(fileId, 'module', name)] = symbol
    }
    for (const [name, rawSymbol] of Object.entries(devices)) {
      const symbol = normalizeSymbolDefinition(
        rawSymbol,
        diagnostics,
        `${symbolUri.fsPath}#devices.${name}`
      )
      symbols[makeSymbolKey(fileId, 'device', name)] = symbol
    }
  }

  return { symbols, diagnostics }
}

export function buildGraphFromDump(
  dump: VisualizerDump,
  diagnostics: string[],
  symbols: Record<string, SymbolDefinition>
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

      const refName = refTarget?.name ?? inst.ref_raw ?? inst.ref_id
      const refFileId = refTarget?.file_id ?? dump.module?.file_id ?? 'unknown'
      const symbolKey = makeSymbolKey(refFileId, inst.ref_kind, refName)
      let symbol = symbols[symbolKey]
      if (!symbol) {
        symbol = buildFallbackSymbol(pins)
        symbols[symbolKey] = symbol
        diagnostics.push(
          `Missing symbol for ${inst.ref_kind} ${refName} (${refFileId}); using default.`
        )
      }
      if (pins.length > 0) {
        validateSymbolPins(symbol, pins, diagnostics, `${inst.ref_kind} ${refName}`)
      }

      return {
        id: inst.inst_id,
        label,
        pins,
        symbolKey
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
    edges,
    symbols
  }
}

export function buildMockGraph(): GraphPayload {
  const mockFileId = 'mock.asdl'
  const deviceSymbolKey = makeSymbolKey(mockFileId, 'device', 'nfet')
  const moduleSymbolKey = makeSymbolKey(mockFileId, 'module', 'buf')
  return {
    moduleId: 'mock_top',
    instances: [
      { id: 'MN1', label: 'MN1', pins: ['D', 'G', 'S', 'B'], symbolKey: deviceSymbolKey },
      { id: 'MP1', label: 'MP1', pins: ['D', 'G', 'S', 'B'], symbolKey: deviceSymbolKey },
      { id: 'XBUF', label: 'XBUF', pins: ['IN', 'OUT'], symbolKey: moduleSymbolKey }
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
    ],
    symbols: {
      [deviceSymbolKey]: {
        body: { ...DEFAULT_SYMBOL_BODY },
        pins: { left: ['D', 'G'], right: ['S', 'B'] }
      },
      [moduleSymbolKey]: {
        body: { w: 8, h: 4 },
        pins: { left: ['IN'], right: ['OUT'] }
      }
    }
  }
}

function collectFileIds(dump: VisualizerDump): Set<string> {
  const fileIds = new Set<string>()
  if (dump.module?.file_id) {
    fileIds.add(dump.module.file_id)
  }
  dump.refs?.modules?.forEach((module) => {
    if (module.file_id) {
      fileIds.add(module.file_id)
    }
  })
  dump.refs?.devices?.forEach((device) => {
    if (device.file_id) {
      fileIds.add(device.file_id)
    }
  })
  return fileIds
}

function resolveSymbolSidecarUri(fileId: string): vscode.Uri {
  const ext = path.extname(fileId)
  const base = ext ? path.basename(fileId, ext) : path.basename(fileId)
  const dir = path.dirname(fileId)
  return vscode.Uri.file(path.join(dir, `${base}.sym.yaml`))
}

function makeSymbolKey(
  fileId: string,
  kind: 'module' | 'device',
  name: string
): string {
  return `${fileId}::${kind}::${name}`
}

function normalizeSymbolDefinition(
  raw: unknown,
  diagnostics: string[],
  context: string
): SymbolDefinition {
  if (!raw || typeof raw !== 'object') {
    diagnostics.push(`Invalid symbol definition at ${context}; using defaults.`)
    return buildFallbackSymbol([])
  }
  const rawSymbol = raw as Record<string, unknown>
  const bodyRaw = rawSymbol.body as { w?: unknown; h?: unknown } | undefined
  const w = normalizeBodyValue(bodyRaw?.w, DEFAULT_SYMBOL_BODY.w, `${context}.body.w`, diagnostics)
  const h = normalizeBodyValue(bodyRaw?.h, DEFAULT_SYMBOL_BODY.h, `${context}.body.h`, diagnostics)

  const pinsRaw = (rawSymbol.pins ?? {}) as Record<string, unknown>
  const pins: SymbolPins = {}
  PIN_SIDES.forEach((side) => {
    const normalized = normalizePinArray(pinsRaw[side], diagnostics, `${context}.pins.${side}`)
    if (normalized.length > 0) {
      pins[side] = normalized
    }
  })

  const pin_offsets = normalizePinOffsets(
    rawSymbol.pin_offsets as Record<string, unknown> | undefined,
    diagnostics,
    `${context}.pin_offsets`
  )
  const glyph = normalizeGlyph(rawSymbol.glyph as Record<string, unknown> | undefined)

  return {
    body: { w, h },
    pins,
    pin_offsets,
    glyph
  }
}

function normalizeBodyValue(
  value: unknown,
  fallback: number,
  context: string,
  diagnostics: string[]
): number {
  if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
    return value
  }
  diagnostics.push(`Invalid ${context}; using ${fallback}.`)
  return fallback
}

function normalizePinArray(
  value: unknown,
  diagnostics: string[],
  context: string
): Array<string | null> {
  if (!Array.isArray(value)) {
    return []
  }
  return value.map((entry, index) => {
    if (entry === null) {
      return null
    }
    if (typeof entry === 'string') {
      return entry
    }
    diagnostics.push(`Invalid pin at ${context}[${index}]; expected string or null.`)
    return null
  })
}

function normalizePinOffsets(
  value: Record<string, unknown> | undefined,
  diagnostics: string[],
  context: string
): SymbolDefinition['pin_offsets'] | undefined {
  if (!value || typeof value !== 'object') {
    return undefined
  }
  const offsets: SymbolDefinition['pin_offsets'] = {}
  PIN_SIDES.forEach((side) => {
    const sideRaw = value[side] as Record<string, unknown> | undefined
    if (!sideRaw || typeof sideRaw !== 'object') {
      return
    }
    const entries: Record<string, number> = {}
    for (const [name, offset] of Object.entries(sideRaw)) {
      if (typeof offset === 'number' && Number.isFinite(offset)) {
        entries[name] = offset
      } else {
        diagnostics.push(`Invalid pin offset at ${context}.${side}.${name}; expected number.`)
      }
    }
    if (Object.keys(entries).length > 0) {
      offsets[side] = entries
    }
  })
  return Object.keys(offsets).length > 0 ? offsets : undefined
}

function normalizeGlyph(
  glyphRaw: Record<string, unknown> | undefined
): SymbolDefinition['glyph'] | undefined {
  if (!glyphRaw || typeof glyphRaw !== 'object') {
    return undefined
  }
  const src = typeof glyphRaw.src === 'string' ? glyphRaw.src : ''
  if (!src) {
    return undefined
  }
  const viewbox = typeof glyphRaw.viewbox === 'string' ? glyphRaw.viewbox : undefined
  return {
    src,
    viewbox
  }
}

function buildFallbackSymbol(pins: string[]): SymbolDefinition {
  const height = Math.max(DEFAULT_SYMBOL_BODY.h, Math.max(1, pins.length - 1))
  return {
    body: { w: DEFAULT_SYMBOL_BODY.w, h: height },
    pins: { left: pins }
  }
}

function collectSymbolPins(pins: SymbolPins): string[] {
  const entries: string[] = []
  PIN_SIDES.forEach((side) => {
    pins[side]?.forEach((pin) => {
      if (typeof pin === 'string') {
        entries.push(pin)
      }
    })
  })
  return entries
}

function validateSymbolPins(
  symbol: SymbolDefinition,
  ports: string[],
  diagnostics: string[],
  context: string
) {
  if (ports.length === 0) {
    return
  }
  const symbolPins = collectSymbolPins(symbol.pins)
  if (symbolPins.length === 0) {
    diagnostics.push(`Symbol pins missing for ${context}.`)
    return
  }
  const symbolSet = new Set(symbolPins)
  const portSet = new Set(ports)
  const missing = ports.filter((pin) => !symbolSet.has(pin))
  const extra = symbolPins.filter((pin) => !portSet.has(pin))
  if (missing.length > 0) {
    diagnostics.push(`Symbol pins missing for ${context}: ${missing.join(', ')}`)
  }
  if (extra.length > 0) {
    diagnostics.push(`Symbol pins not in ports for ${context}: ${extra.join(', ')}`)
  }
}
