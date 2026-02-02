import path from 'path'
import * as vscode from 'vscode'
import YAML from 'yaml'

import { fileExists } from './util'
import type {
  GraphPayload,
  SymbolDefinition,
  SymbolGlyph,
  SymbolPin,
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
  dump: VisualizerDump,
  webview: vscode.Webview
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
      const symbol = await normalizeSymbolDefinition(
        rawSymbol,
        diagnostics,
        `${symbolUri.fsPath}#modules.${name}`,
        fileId,
        webview
      )
      symbols[makeSymbolKey(fileId, 'module', name)] = symbol
    }
    for (const [name, rawSymbol] of Object.entries(devices)) {
      const symbol = await normalizeSymbolDefinition(
        rawSymbol,
        diagnostics,
        `${symbolUri.fsPath}#devices.${name}`,
        fileId,
        webview
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

  const instanceLabelCounts = new Map<string, number>()
  dump.instances?.forEach((inst) => {
    const label = resolveExprRaw(inst.name_expr_id) || inst.ref_raw || inst.inst_id
    if (!label) {
      return
    }
    instanceLabelCounts.set(label, (instanceLabelCounts.get(label) ?? 0) + 1)
  })
  instanceLabelCounts.forEach((count, label) => {
    if (count > 1) {
      diagnostics.push(
        `Duplicate instance name "${label}" appears ${count} times; layout keys will use "${label}#<id>".`
      )
    }
  })

  const netLabelCounts = new Map<string, number>()
  dump.nets?.forEach((net) => {
    const label = resolveExprRaw(net.name_expr_id) || net.net_id
    if (!label) {
      return
    }
    netLabelCounts.set(label, (netLabelCounts.get(label) ?? 0) + 1)
  })
  netLabelCounts.forEach((count, label) => {
    if (count > 1) {
      diagnostics.push(
        `Duplicate net name "${label}" appears ${count} times; layout keys will use "${label}#<id>".`
      )
    }
  })

  const layoutKeyForLabel = (
    label: string,
    fallbackId: string,
    counts: Map<string, number>
  ) => {
    if (!label) {
      return fallbackId
    }
    const count = counts.get(label) ?? 0
    if (count > 1) {
      return `${label}#${fallbackId}`
    }
    return label
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
        symbolKey,
        layoutKey: layoutKeyForLabel(label, inst.inst_id, instanceLabelCounts)
      }
    }) ?? []

  const netHubs =
    dump.nets?.map((net) => {
      const label = resolveExprRaw(net.name_expr_id) || net.net_id
      return {
        id: net.net_id,
        label,
        layoutKey: layoutKeyForLabel(label, net.net_id, netLabelCounts)
      }
    }) ?? []

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
        to: endpoint.net_id,
        conn_label: endpoint.conn_label
      }
    }) ?? []

  return {
    moduleId: dump.module.name,
    instances,
    netHubs,
    edges,
    symbols,
    schematic_hints: dump.registries?.schematic_hints ?? null
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
        pins: {
          left: [
            { name: 'D', offset: 0, visible: true },
            { name: 'G', offset: 0, visible: true }
          ],
          right: [
            { name: 'S', offset: 0, visible: true },
            { name: 'B', offset: 0, visible: true }
          ]
        }
      },
      [moduleSymbolKey]: {
        body: { w: 8, h: 4 },
        pins: {
          left: [{ name: 'IN', offset: 0, visible: true }],
          right: [{ name: 'OUT', offset: 0, visible: true }]
        }
      }
    }
  }
}

export function collectFileIds(dump: VisualizerDump): Set<string> {
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

async function normalizeSymbolDefinition(
  raw: unknown,
  diagnostics: string[],
  context: string,
  fileId: string,
  webview: vscode.Webview
): Promise<SymbolDefinition> {
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

  const glyph = await normalizeGlyph(
    rawSymbol.glyph as Record<string, unknown> | undefined,
    diagnostics,
    `${context}.glyph`,
    fileId,
    webview
  )

  return {
    body: { w, h },
    pins,
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
): Array<SymbolPin | null> {
  if (!Array.isArray(value)) {
    return []
  }
  return value.map((entry, index) => {
    if (entry === null) {
      return null
    }
    if (typeof entry === 'string') {
      return { name: entry, offset: 0, visible: true, connect_by_label: false }
    }
    if (typeof entry === 'object' && entry !== null && !Array.isArray(entry)) {
      const keys = Object.keys(entry as Record<string, unknown>)
      if (keys.length !== 1) {
        diagnostics.push(`Invalid pin at ${context}[${index}]; expected single-key map.`)
        return null
      }
      const pinName = keys[0]
      const metadata = (entry as Record<string, unknown>)[pinName]
      if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) {
        diagnostics.push(
          `Invalid pin metadata at ${context}[${index}]; expected object for ${pinName}.`
        )
        return { name: pinName, offset: 0, visible: true }
      }
      const metaRecord = metadata as Record<string, unknown>
      let offset = 0
      if (metaRecord.offset !== undefined) {
        if (typeof metaRecord.offset === 'number' && Number.isFinite(metaRecord.offset)) {
          offset = metaRecord.offset
        } else {
          diagnostics.push(
            `Invalid pin offset at ${context}[${index}]; expected number for ${pinName}.`
          )
        }
      }
      let visible = true
      if (metaRecord.visible !== undefined) {
        if (typeof metaRecord.visible === 'boolean') {
          visible = metaRecord.visible
        } else {
          diagnostics.push(
            `Invalid pin visibility at ${context}[${index}]; expected boolean for ${pinName}.`
          )
        }
      }
      let connectByLabel = false
      if (metaRecord.connect_by_label !== undefined) {
        if (typeof metaRecord.connect_by_label === 'boolean') {
          connectByLabel = metaRecord.connect_by_label
        } else {
          diagnostics.push(
            `Invalid connect_by_label at ${context}[${index}]; expected boolean for ${pinName}.`
          )
        }
      }
      return { name: pinName, offset, visible, connect_by_label: connectByLabel }
    }
    diagnostics.push(
      `Invalid pin at ${context}[${index}]; expected string, null, or pin metadata map.`
    )
    return null
  })
}

async function normalizeGlyph(
  glyphRaw: Record<string, unknown> | undefined,
  diagnostics: string[],
  context: string,
  fileId: string,
  webview: vscode.Webview
): Promise<SymbolDefinition['glyph'] | undefined> {
  if (!glyphRaw || typeof glyphRaw !== 'object') {
    return undefined
  }
  const src = typeof glyphRaw.src === 'string' ? glyphRaw.src : ''
  if (!src) {
    return undefined
  }
  const viewbox = typeof glyphRaw.viewbox === 'string' ? glyphRaw.viewbox : undefined
  const boxRaw = glyphRaw.box as Record<string, unknown> | undefined
  const box = normalizeGlyphBox(boxRaw, diagnostics, `${context}.box`)
  if (!box) {
    return undefined
  }
  const resolvedSrc = await resolveGlyphSource(src, fileId, webview, diagnostics, context)
  if (!resolvedSrc) {
    return undefined
  }
  return {
    src: resolvedSrc,
    viewbox,
    box
  }
}

async function resolveGlyphSource(
  src: string,
  fileId: string,
  webview: vscode.Webview,
  diagnostics: string[],
  context: string
): Promise<string | null> {
  const baseDir = path.dirname(fileId)
  const resolvedPath = path.isAbsolute(src) ? src : path.resolve(baseDir, src)
  const glyphUri = vscode.Uri.file(resolvedPath)
  if (!(await fileExists(glyphUri))) {
    diagnostics.push(`Missing glyph asset at ${resolvedPath} for ${context}.`)
    return null
  }
  return webview.asWebviewUri(glyphUri).toString()
}

function normalizeGlyphBox(
  value: Record<string, unknown> | undefined,
  diagnostics: string[],
  context: string
): SymbolGlyph['box'] | null {
  if (!value || typeof value !== 'object') {
    diagnostics.push(`Missing glyph box at ${context}.`)
    return null
  }
  const x = normalizeGlyphBoxValue(value.x, `${context}.x`, diagnostics)
  const y = normalizeGlyphBoxValue(value.y, `${context}.y`, diagnostics)
  const w = normalizeGlyphBoxSize(value.w, `${context}.w`, diagnostics)
  const h = normalizeGlyphBoxSize(value.h, `${context}.h`, diagnostics)
  if (x === null || y === null || w === null || h === null) {
    return null
  }
  return { x, y, w, h }
}

function normalizeGlyphBoxValue(
  value: unknown,
  context: string,
  diagnostics: string[]
): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  diagnostics.push(`Invalid ${context}; expected number.`)
  return null
}

function normalizeGlyphBoxSize(
  value: unknown,
  context: string,
  diagnostics: string[]
): number | null {
  if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
    return value
  }
  diagnostics.push(`Invalid ${context}; expected positive number.`)
  return null
}

function buildFallbackSymbol(pins: string[]): SymbolDefinition {
  const height = Math.max(DEFAULT_SYMBOL_BODY.h, Math.max(1, pins.length - 1))
  return {
    body: { w: DEFAULT_SYMBOL_BODY.w, h: height },
    pins: {
      left: pins.map((pin) => ({ name: pin, offset: 0, visible: true, connect_by_label: false }))
    }
  }
}

function collectSymbolPins(pins: SymbolPins): string[] {
  const entries: string[] = []
  PIN_SIDES.forEach((side) => {
    pins[side]?.forEach((pin) => {
      if (pin && typeof pin === 'object') {
        entries.push(pin.name)
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
