import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import path from 'node:path'
import fs from 'node:fs/promises'
import YAML from 'yaml'

const execFileAsync = promisify(execFile)
const DEFAULT_BODY = { w: 6, h: 4 }
const DEFAULT_GRID = 16

const args = process.argv.slice(2)
if (args.length === 0) {
  console.error('Usage: node scripts/build-dev-payload.mjs --asdl <file> [--module name] [--out file]')
  process.exit(1)
}

const parsed = parseArgs(args)
const asdlPath = parsed.asdl ?? parsed._[0]
if (!asdlPath) {
  console.error('Missing --asdl <file>')
  process.exit(1)
}
const resolvedAsdl = path.resolve(asdlPath)
const outPath = path.resolve(parsed.out ?? path.join('src', 'webview', 'public', 'dev_payload.json'))

const moduleName = parsed.module ?? (await pickFirstModule(resolvedAsdl))
if (!moduleName) {
  console.error('No modules found in entry file.')
  process.exit(1)
}

const dump = await loadVisualizerDump(resolvedAsdl, moduleName)
const symbols = await loadSymbolLibrary(dump)
const graph = buildGraphFromDump(dump, symbols)
const layout = await loadLayout(resolvedAsdl, moduleName, graph)

await fs.mkdir(path.dirname(outPath), { recursive: true })
await fs.writeFile(outPath, JSON.stringify({ graph, layout }, null, 2))
console.log(`Wrote dev payload to ${outPath}`)

function parseArgs(argv) {
  const result = { _: [] }
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i]
    if (!value.startsWith('--')) {
      result._.push(value)
      continue
    }
    const key = value.slice(2)
    const next = argv[i + 1]
    if (next && !next.startsWith('--')) {
      result[key] = next
      i += 1
    } else {
      result[key] = true
    }
  }
  return result
}

async function runAsdlc(args, cwd) {
  const { stdout } = await execFileAsync('asdlc', args, {
    cwd,
    encoding: 'utf8',
    maxBuffer: 10 * 1024 * 1024
  })
  return stdout
}

async function pickFirstModule(asdlFile) {
  const stdout = await runAsdlc(
    ['visualizer-dump', asdlFile, '--list-modules', '--compact'],
    path.dirname(asdlFile)
  )
  const payload = JSON.parse(stdout)
  return payload?.modules?.[0]?.name ?? null
}

async function loadVisualizerDump(asdlFile, moduleName) {
  const stdout = await runAsdlc(
    ['visualizer-dump', asdlFile, '--module', moduleName, '--compact'],
    path.dirname(asdlFile)
  )
  return JSON.parse(stdout)
}

async function loadSymbolLibrary(dump) {
  const symbols = {}
  const fileIds = collectFileIds(dump)
  for (const fileId of fileIds) {
    const symbolPath = resolveSymbolSidecarPath(fileId)
    if (!(await exists(symbolPath))) {
      continue
    }
    const raw = await fs.readFile(symbolPath, 'utf8')
    const payload = YAML.parse(raw)
    if (!payload || typeof payload !== 'object') {
      continue
    }
    const modules = payload.modules ?? {}
    const devices = payload.devices ?? {}
    for (const [name, rawSymbol] of Object.entries(modules)) {
      symbols[makeSymbolKey(fileId, 'module', name)] = await normalizeSymbol(
        rawSymbol,
        fileId
      )
    }
    for (const [name, rawSymbol] of Object.entries(devices)) {
      symbols[makeSymbolKey(fileId, 'device', name)] = await normalizeSymbol(
        rawSymbol,
        fileId
      )
    }
  }
  return symbols
}

async function normalizeSymbol(raw, fileId) {
  if (!raw || typeof raw !== 'object') {
    return buildFallbackSymbol([])
  }
  const bodyRaw = raw.body ?? {}
  const w =
    typeof bodyRaw.w === 'number' && Number.isFinite(bodyRaw.w) && bodyRaw.w > 0
      ? bodyRaw.w
      : DEFAULT_BODY.w
  const h =
    typeof bodyRaw.h === 'number' && Number.isFinite(bodyRaw.h) && bodyRaw.h > 0
      ? bodyRaw.h
      : DEFAULT_BODY.h

  const pins = {}
  const pinsRaw = raw.pins ?? {}
  for (const side of ['top', 'bottom', 'left', 'right']) {
    const entries = normalizePinArray(pinsRaw[side])
    if (entries.length > 0) {
      pins[side] = entries
    }
  }

  const glyph = await normalizeGlyph(raw.glyph, fileId)
  return { body: { w, h }, pins, glyph }
}

function normalizePinArray(value) {
  if (!Array.isArray(value)) {
    return []
  }
  return value.map((entry) => {
    if (entry === null) {
      return null
    }
    if (typeof entry === 'string') {
      return { name: entry, offset: 0, visible: true }
    }
    if (typeof entry === 'object' && entry !== null && !Array.isArray(entry)) {
      const keys = Object.keys(entry)
      if (keys.length !== 1) {
        return null
      }
      const pinName = keys[0]
      const meta = entry[pinName]
      if (!meta || typeof meta !== 'object' || Array.isArray(meta)) {
        return { name: pinName, offset: 0, visible: true }
      }
      const offset =
        typeof meta.offset === 'number' && Number.isFinite(meta.offset) ? meta.offset : 0
      const visible =
        typeof meta.visible === 'boolean' ? meta.visible : true
      return { name: pinName, offset, visible }
    }
    return null
  })
}

async function normalizeGlyph(glyphRaw, fileId) {
  if (!glyphRaw || typeof glyphRaw !== 'object') {
    return undefined
  }
  if (typeof glyphRaw.src !== 'string' || glyphRaw.src.length === 0) {
    return undefined
  }
  const box = normalizeGlyphBox(glyphRaw.box)
  if (!box) {
    return undefined
  }
  const src = await resolveGlyphSource(glyphRaw.src, fileId)
  if (!src) {
    return undefined
  }
  const viewbox = typeof glyphRaw.viewbox === 'string' ? glyphRaw.viewbox : undefined
  return { src, viewbox, box }
}

function normalizeGlyphBox(value) {
  if (!value || typeof value !== 'object') {
    return null
  }
  const x = Number.isFinite(value.x) ? value.x : null
  const y = Number.isFinite(value.y) ? value.y : null
  const w = Number.isFinite(value.w) && value.w > 0 ? value.w : null
  const h = Number.isFinite(value.h) && value.h > 0 ? value.h : null
  if (x === null || y === null || w === null || h === null) {
    return null
  }
  return { x, y, w, h }
}

async function resolveGlyphSource(src, fileId) {
  const baseDir = path.dirname(fileId)
  const resolved = path.isAbsolute(src) ? src : path.resolve(baseDir, src)
  if (!(await exists(resolved))) {
    return null
  }
  const ext = path.extname(resolved).toLowerCase()
  const data = await fs.readFile(resolved)
  if (ext === '.svg') {
    const svg = data.toString('utf8')
    return `data:image/svg+xml,${encodeURIComponent(svg)}`
  }
  const mime = ext === '.png' ? 'image/png' : ext === '.jpg' || ext === '.jpeg' ? 'image/jpeg' : ''
  if (!mime) {
    return null
  }
  return `data:${mime};base64,${data.toString('base64')}`
}

function buildGraphFromDump(dump, symbols) {
  const patternExpressions = dump.registries?.pattern_expressions ?? {}
  const devices = new Map((dump.refs?.devices ?? []).map((d) => [d.device_id, d]))
  const modules = new Map((dump.refs?.modules ?? []).map((m) => [m.module_id, m]))

  const resolveExprRaw = (exprId) => {
    if (!exprId) {
      return ''
    }
    const raw = patternExpressions[exprId]?.raw
    return typeof raw === 'string' && raw.length > 0 ? raw : exprId
  }

  const instNameToId = new Map()
  const instances = (dump.instances ?? []).map((inst) => {
    const label = resolveExprRaw(inst.name_expr_id) || inst.ref_raw || inst.inst_id
    if (label) {
      instNameToId.set(label, inst.inst_id)
    }
    const refTarget = inst.ref_kind === 'device' ? devices.get(inst.ref_id) : modules.get(inst.ref_id)
    const pins = refTarget?.ports ?? []
    const refName = refTarget?.name ?? inst.ref_raw ?? inst.ref_id
    const refFileId = refTarget?.file_id ?? dump.module?.file_id ?? 'unknown'
    const symbolKey = makeSymbolKey(refFileId, inst.ref_kind, refName)
    if (!symbols[symbolKey]) {
      symbols[symbolKey] = buildFallbackSymbol(pins)
    }
    return { id: inst.inst_id, label, pins, symbolKey }
  })

  const netHubs = (dump.nets ?? []).map((net) => ({
    id: net.net_id,
    label: resolveExprRaw(net.name_expr_id) || net.net_id
  }))

  const edges = (dump.endpoints ?? []).map((endpoint) => {
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
    return { id: endpoint.endpoint_id, from, to: endpoint.net_id }
  })

  return {
    moduleId: dump.module?.name ?? 'unknown',
    instances,
    netHubs,
    edges,
    symbols
  }
}

async function loadLayout(asdlFile, moduleName, graph) {
  const dir = path.dirname(asdlFile)
  const base = path.basename(asdlFile, '.asdl')
  const layoutPath = path.join(dir, `${base}.sch.yaml`)
  let layout = null
  if (await exists(layoutPath)) {
    const raw = await fs.readFile(layoutPath, 'utf8')
    try {
      layout = YAML.parse(raw)
    } catch {
      layout = null
    }
  }
  const merged = layout ?? { schema_version: 0, modules: {} }
  if (!merged.schema_version) {
    merged.schema_version = 0
  }
  if (!merged.modules) {
    merged.modules = {}
  }
  merged.modules[moduleName] = mergeLayoutModule(merged.modules[moduleName], graph)
  return merged
}

function mergeLayoutModule(existing, graph) {
  const gridSize = existing?.grid_size ?? DEFAULT_GRID
  const moduleLayout = existing ?? {
    grid_size: gridSize,
    instances: {},
    net_hubs: {}
  }
  moduleLayout.instances = moduleLayout.instances ?? {}
  moduleLayout.net_hubs = moduleLayout.net_hubs ?? {}

  const instIds = graph.instances.map((inst) => inst.id)
  const hubIds = graph.netHubs.map((hub) => hub.id)
  const cols = Math.max(1, Math.ceil(Math.sqrt(instIds.length || 1)))
  const xStep = 4
  const yStep = 4

  instIds.forEach((instId, index) => {
    if (!moduleLayout.instances[instId]) {
      moduleLayout.instances[instId] = {
        x: (index % cols) * xStep,
        y: Math.floor(index / cols) * yStep,
        orient: 'R0'
      }
    }
  })

  hubIds.forEach((hubId, index) => {
    if (!moduleLayout.net_hubs[hubId]) {
      moduleLayout.net_hubs[hubId] = {
        groups: [
          {
            x: (cols + 2) * xStep,
            y: index * yStep
          }
        ]
      }
    }
  })

  moduleLayout.grid_size = gridSize
  return moduleLayout
}

function collectFileIds(dump) {
  const fileIds = new Set()
  if (dump.module?.file_id) {
    fileIds.add(dump.module.file_id)
  }
  for (const module of dump.refs?.modules ?? []) {
    if (module.file_id) {
      fileIds.add(module.file_id)
    }
  }
  for (const device of dump.refs?.devices ?? []) {
    if (device.file_id) {
      fileIds.add(device.file_id)
    }
  }
  return fileIds
}

function resolveSymbolSidecarPath(fileId) {
  const ext = path.extname(fileId)
  const base = ext ? path.basename(fileId, ext) : path.basename(fileId)
  const dir = path.dirname(fileId)
  return path.join(dir, `${base}.sym.yaml`)
}

function makeSymbolKey(fileId, kind, name) {
  return `${fileId}::${kind}::${name}`
}

function buildFallbackSymbol(pins) {
  const height = Math.max(DEFAULT_BODY.h, Math.max(1, pins.length - 1))
  return {
    body: { w: DEFAULT_BODY.w, h: height },
    pins: { left: pins.map((pin) => ({ name: pin, offset: 0, visible: true })) }
  }
}

async function exists(filePath) {
  try {
    await fs.access(filePath)
    return true
  } catch {
    return false
  }
}
