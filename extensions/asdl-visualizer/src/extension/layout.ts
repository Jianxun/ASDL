import path from 'path'
import * as vscode from 'vscode'
import YAML from 'yaml'

import { fileExists } from './util'
import type { GraphPayload, LayoutPayload } from './types'

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
          net_vdd: { groups: [{ x: 10, y: 0 }] },
          net_vss: { groups: [{ x: 10, y: 8 }] },
          net_out: { groups: [{ x: 10, y: 4 }] }
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
