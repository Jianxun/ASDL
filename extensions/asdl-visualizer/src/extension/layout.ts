import path from 'path'
import * as vscode from 'vscode'
import YAML from 'yaml'

import { fileExists } from './util'
import type { GraphPayload, HubPlacement, LayoutPayload, NetHubEntry, NetTopology } from './types'

export async function writeLayoutSidecar(asdlUri: vscode.Uri, layoutYaml: string) {
  const dir = path.dirname(asdlUri.fsPath)
  const base = path.basename(asdlUri.fsPath, '.asdl')
  const outPath = path.join(dir, `${base}.sch.yaml`)
  const outUri = vscode.Uri.file(outPath)
  const payload = layoutYaml.endsWith('\n') ? layoutYaml : `${layoutYaml}\n`
  await vscode.workspace.fs.writeFile(outUri, Buffer.from(payload, 'utf8'))
}

export async function readLayoutSidecar(
  asdlUri: vscode.Uri,
  graph: GraphPayload,
  moduleName: string
): Promise<LayoutPayload> {
  const dir = path.dirname(asdlUri.fsPath)
  const base = path.basename(asdlUri.fsPath, '.asdl')
  const layoutUri = vscode.Uri.file(path.join(dir, `${base}.sch.yaml`))

  let layout: LayoutPayload | null = null
  if (await fileExists(layoutUri)) {
    const raw = await vscode.workspace.fs.readFile(layoutUri)
    const text = Buffer.from(raw).toString('utf8')
    try {
      layout = YAML.parse(text) as LayoutPayload
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

  merged.modules[moduleName] = mergeLayoutModule(
    merged.modules[moduleName],
    graph
  )
  return merged
}

export function buildMockLayout(): LayoutPayload {
  return {
    schema_version: 0,
    modules: {
      mock_top: {
        grid_size: 16,
        instances: {
          MN1: { x: 6, y: 6, orient: 'R0' },
          MP1: { x: 6, y: 2, orient: 'MX' },
          XBUF: { x: 2, y: 4, orient: 'R0' }
        },
        net_hubs: {
          net_vdd: { topology: 'star', hubs: { hub1: { x: 10, y: 0 } } },
          net_vss: { topology: 'star', hubs: { hub1: { x: 10, y: 8 } } },
          net_out: { topology: 'star', hubs: { hub1: { x: 10, y: 4 } } }
        }
      }
    }
  }
}

function mergeLayoutModule(
  existing: LayoutPayload['modules'][string] | undefined,
  graph: GraphPayload
): LayoutPayload['modules'][string] {
  const gridSize = existing?.grid_size ?? 16
  const moduleLayout = existing ?? {
    grid_size: gridSize,
    instances: {},
    net_hubs: {}
  }
  if (!moduleLayout.instances) {
    moduleLayout.instances = {}
  }
  if (!moduleLayout.net_hubs) {
    moduleLayout.net_hubs = {}
  }

  const instKeys = graph.instances.map((inst) => inst.layoutKey ?? inst.id)
  const cols = Math.max(1, Math.ceil(Math.sqrt(instKeys.length || 1)))
  const xStep = 4
  const yStep = 4
  let hubRowIndex = 0

  graph.instances.forEach((inst, index) => {
    const instKey = inst.layoutKey ?? inst.id
    const fallbackId = inst.id
    const existingPlacement = moduleLayout.instances[instKey] ?? moduleLayout.instances[fallbackId]
    if (!moduleLayout.instances[instKey]) {
      moduleLayout.instances[instKey] = existingPlacement ?? {
        x: (index % cols) * xStep,
        y: Math.floor(index / cols) * yStep,
        orient: 'R0'
      }
      if (fallbackId !== instKey && moduleLayout.instances[fallbackId]) {
        delete moduleLayout.instances[fallbackId]
      }
    }
  })

  graph.netHubs.forEach((hub) => {
    const hubKey = hub.layoutKey ?? hub.id
    const fallbackId = hub.id
    const existingHubRaw = moduleLayout.net_hubs[hubKey] ?? moduleLayout.net_hubs[fallbackId]
    const normalizedHub = normalizeNetHubEntry(existingHubRaw)
    const groupCount = resolveHubGroupCount(graph, hub.id)
    const entry = ensureHubCount(
      normalizedHub ?? { topology: DEFAULT_TOPOLOGY, hubs: {} },
      groupCount,
      (groupIndex) => ({
        x: (cols + 2) * xStep,
        y: (hubRowIndex + groupIndex) * yStep
      })
    )
    moduleLayout.net_hubs[hubKey] = entry
    if (fallbackId !== hubKey && moduleLayout.net_hubs[fallbackId]) {
      delete moduleLayout.net_hubs[fallbackId]
    }
    hubRowIndex += groupCount
  })

  moduleLayout.grid_size = gridSize
  return moduleLayout
}

const DEFAULT_TOPOLOGY: NetTopology = 'star'

function resolveHubGroupCount(graph: GraphPayload, netId: string): number {
  const groups = graph.schematic_hints?.net_groups?.[netId]
  if (Array.isArray(groups) && groups.length > 0) {
    return groups.length
  }
  return 1
}

function normalizeNetHubEntry(value: unknown): NetHubEntry | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null
  }
  const record = value as Record<string, unknown>
  const hasHubs = Object.prototype.hasOwnProperty.call(record, 'hubs')
  const hasTopology = Object.prototype.hasOwnProperty.call(record, 'topology')
  if (hasHubs || hasTopology) {
    const hubs = toPlacementMap(hasHubs ? record.hubs : {}) ?? {}
    return {
      topology: normalizeTopology(record.topology),
      hubs
    }
  }
  const legacy = toPlacementMap(record)
  if (!legacy) {
    return null
  }
  return { topology: DEFAULT_TOPOLOGY, hubs: legacy }
}

function normalizeTopology(value: unknown): NetTopology {
  if (value === 'star' || value === 'mst' || value === 'trunk') {
    return value
  }
  return DEFAULT_TOPOLOGY
}

function toPlacementMap(value: unknown): Record<string, HubPlacement> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null
  }
  const result: Record<string, HubPlacement> = {}
  Object.entries(value as Record<string, unknown>).forEach(([key, entry]) => {
    if (isPlacement(entry)) {
      result[key] = entry
    }
  })
  return result
}

function isPlacement(value: unknown): value is HubPlacement {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return false
  }
  const candidate = value as { x?: number; y?: number }
  return Number.isFinite(candidate.x) && Number.isFinite(candidate.y)
}

function ensureHubCount(
  entry: NetHubEntry,
  desiredCount: number,
  makeDefault: (index: number) => HubPlacement
): NetHubEntry {
  const hubs = entry.hubs ?? {}
  const existingKeys = Object.keys(hubs)
  const used = new Set(existingKeys)
  for (let index = existingKeys.length; index < desiredCount; index += 1) {
    const hubName = nextHubName(used, index + 1)
    hubs[hubName] = makeDefault(index)
    used.add(hubName)
  }
  return {
    topology: normalizeTopology(entry.topology),
    hubs
  }
}

function nextHubName(used: Set<string>, startIndex: number): string {
  let index = startIndex
  while (true) {
    const candidate = `hub${index}`
    if (!used.has(candidate)) {
      return candidate
    }
    index += 1
  }
}
