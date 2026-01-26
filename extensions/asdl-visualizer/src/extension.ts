import * as vscode from 'vscode'
import path from 'path'
import YAML from 'yaml'

const VIEW_TYPE = 'asdlVisualizer'

export function activate(context: vscode.ExtensionContext) {
  const command = vscode.commands.registerCommand('asdl.openVisualizer', async () => {
    const asdlUri = resolveActiveAsdlUri()
    if (!asdlUri) {
      vscode.window.showErrorMessage('Open an .asdl file before launching the visualizer.')
      return
    }

    const panel = vscode.window.createWebviewPanel(
      VIEW_TYPE,
      'ASDL Visualizer',
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        retainContextWhenHidden: true
      }
    )

    panel.webview.html = await getWebviewHtml(panel.webview, context.extensionUri)

    panel.webview.onDidReceiveMessage(async (message) => {
      if (message?.type === 'ready') {
        try {
          const payload = await loadGraphPayload(asdlUri, context)
          panel.webview.postMessage({ type: 'loadGraph', payload })
          panel.webview.postMessage({
            type: 'diagnostics',
            payload: { items: payload.diagnostics }
          })
        } catch (error) {
          const details = error instanceof Error ? error.message : String(error)
          panel.webview.postMessage({
            type: 'loadGraph',
            payload: {
              graph: buildMockGraph(),
              layout: buildMockLayout(),
              diagnostics: [`Failed to load PatternedGraph: ${details}`]
            }
          })
          panel.webview.postMessage({
            type: 'diagnostics',
            payload: { items: [`Failed to load PatternedGraph: ${details}`] }
          })
          vscode.window.showErrorMessage(`ASDL visualizer load failed: ${details}`)
        }
      }

      if (message?.type === 'saveLayout') {
        try {
          const layoutYaml = YAML.stringify(message.payload.layout)
          await writeLayoutSidecar(asdlUri, layoutYaml)
          vscode.window.showInformationMessage('ASDL visualizer layout saved.')
        } catch (error) {
          const details = error instanceof Error ? error.message : String(error)
          vscode.window.showErrorMessage(`Failed to save layout: ${details}`)
        }
      }
    })
  })

  context.subscriptions.push(command)
}

export function deactivate() {
  return undefined
}

function resolveActiveAsdlUri(): vscode.Uri | null {
  const editor = vscode.window.activeTextEditor
  if (!editor) {
    return null
  }
  const uri = editor.document.uri
  if (path.extname(uri.fsPath) !== '.asdl') {
    return null
  }
  return uri
}

type PatternedGraphDump = {
  modules?: Array<{
    module_id: string
    name: string
    file_id: string
    ports?: string[]
    nets?: Array<{
      net_id: string
      name_expr_id: string
      endpoint_ids?: string[]
    }>
    instances?: Array<{
      inst_id: string
      name_expr_id: string
      ref_kind: 'module' | 'device'
      ref_id: string
      ref_raw?: string
    }>
    endpoints?: Array<{
      endpoint_id: string
      net_id: string
      port_expr_id: string
    }>
  }>
  devices?: Array<{
    device_id: string
    name: string
    file_id: string
    ports?: string[]
  }>
  registries?: {
    pattern_expressions?: Record<string, { raw?: string }>
  }
}

type GraphPayload = {
  moduleId: string
  instances: Array<{ id: string; label: string; pins: string[] }>
  netHubs: Array<{ id: string; label: string }>
  edges: Array<{ id: string; from: string; to: string }>
}

type LayoutPayload = {
  schema_version: number
  modules: Record<
    string,
    {
      grid_size?: number
      instances: Record<string, { x: number; y: number; orient?: string; label?: string }>
      net_hubs: Record<string, { groups: Array<{ x: number; y: number; orient?: string; label?: string }> }>
    }
  >
}

type LoadGraphPayload = {
  graph: GraphPayload
  layout: LayoutPayload
  diagnostics: string[]
}

async function writeLayoutSidecar(asdlUri: vscode.Uri, layoutYaml: string) {
  const dir = path.dirname(asdlUri.fsPath)
  const base = path.basename(asdlUri.fsPath, '.asdl')
  const outPath = path.join(dir, `${base}.sch.yaml`)
  const outUri = vscode.Uri.file(outPath)
  const payload = layoutYaml.endsWith('\n') ? layoutYaml : `${layoutYaml}\n`
  await vscode.workspace.fs.writeFile(outUri, Buffer.from(payload, 'utf8'))
}

async function loadGraphPayload(
  asdlUri: vscode.Uri,
  context: vscode.ExtensionContext
): Promise<LoadGraphPayload> {
  const diagnostics: string[] = []
  const graphUri = await resolvePatternedGraphUri(asdlUri, context)
  if (!graphUri) {
    throw new Error('PatternedGraph JSON not selected.')
  }
  const dump = await readPatternedGraphDump(graphUri)
  const moduleDump = await selectModuleDump(dump, asdlUri, diagnostics)
  const graph = buildGraphFromDump(dump, moduleDump, diagnostics)
  const layout = await readLayoutSidecar(asdlUri, graph, moduleDump.name)
  return { graph, layout, diagnostics }
}

async function resolvePatternedGraphUri(
  asdlUri: vscode.Uri,
  context: vscode.ExtensionContext
): Promise<vscode.Uri | null> {
  const cacheKey = `asdlVisualizer.graphDump:${asdlUri.fsPath}`
  const cachedPath = context.workspaceState.get<string>(cacheKey)
  if (cachedPath && (await fileExists(vscode.Uri.file(cachedPath)))) {
    return vscode.Uri.file(cachedPath)
  }

  const dir = path.dirname(asdlUri.fsPath)
  const base = path.basename(asdlUri.fsPath, '.asdl')
  const candidates = [
    path.join(dir, `${base}.patterned.json`),
    path.join(dir, `${base}.patterned-graph.json`),
    path.join(dir, `${base}.patterned_graph.json`)
  ]
  for (const candidate of candidates) {
    const uri = vscode.Uri.file(candidate)
    if (await fileExists(uri)) {
      await context.workspaceState.update(cacheKey, candidate)
      return uri
    }
  }

  const picked = await vscode.window.showOpenDialog({
    canSelectMany: false,
    openLabel: 'Select PatternedGraph JSON',
    filters: { JSON: ['json'] },
    defaultUri: vscode.Uri.file(dir)
  })
  if (!picked || picked.length === 0) {
    return null
  }
  await context.workspaceState.update(cacheKey, picked[0].fsPath)
  return picked[0]
}

async function fileExists(uri: vscode.Uri): Promise<boolean> {
  try {
    await vscode.workspace.fs.stat(uri)
    return true
  } catch {
    return false
  }
}

async function readPatternedGraphDump(uri: vscode.Uri): Promise<PatternedGraphDump> {
  const raw = await vscode.workspace.fs.readFile(uri)
  const text = Buffer.from(raw).toString('utf8')
  return JSON.parse(text) as PatternedGraphDump
}

async function selectModuleDump(
  dump: PatternedGraphDump,
  asdlUri: vscode.Uri,
  diagnostics: string[]
): Promise<NonNullable<PatternedGraphDump['modules']>[number]> {
  const modules = dump.modules ?? []
  if (modules.length === 0) {
    throw new Error('PatternedGraph dump contains no modules.')
  }

  const asdlPath = path.resolve(asdlUri.fsPath)
  const basename = path.basename(asdlPath)
  const matching = modules.filter((module) => {
    if (!module.file_id) {
      return false
    }
    if (module.file_id === asdlUri.fsPath) {
      return true
    }
    try {
      if (path.resolve(module.file_id) === asdlPath) {
        return true
      }
    } catch {
      // ignore path resolution errors
    }
    return path.basename(module.file_id) === basename
  })

  if (matching.length === 1) {
    return matching[0]
  }

  const candidates = matching.length > 0 ? matching : modules
  if (matching.length === 0) {
    diagnostics.push(
      'PatternedGraph dump does not match the active file; showing first module.'
    )
  }

  if (candidates.length === 1) {
    return candidates[0]
  }

  const picked = await vscode.window.showQuickPick(
    candidates.map((module) => ({
      label: module.name,
      description: module.file_id,
      module
    })),
    { placeHolder: 'Select ASDL module to visualize' }
  )
  if (!picked) {
    return candidates[0]
  }
  return picked.module
}

function buildGraphFromDump(
  dump: PatternedGraphDump,
  moduleDump: NonNullable<PatternedGraphDump['modules']>[number],
  diagnostics: string[]
): GraphPayload {
  const patternExpressions = dump.registries?.pattern_expressions ?? {}
  const devices = new Map((dump.devices ?? []).map((device) => [device.device_id, device]))
  const modules = new Map((dump.modules ?? []).map((module) => [module.module_id, module]))

  const resolveExprRaw = (exprId: string | undefined) => {
    if (!exprId) {
      return ''
    }
    const raw = patternExpressions[exprId]?.raw
    return typeof raw === 'string' && raw.length > 0 ? raw : exprId
  }

  const instNameToId = new Map<string, string>()
  const instances =
    moduleDump.instances?.map((inst) => {
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
    moduleDump.nets?.map((net) => ({
      id: net.net_id,
      label: resolveExprRaw(net.name_expr_id) || net.net_id
    })) ?? []

  const edges =
    moduleDump.endpoints?.map((endpoint) => {
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
    moduleId: moduleDump.name,
    instances,
    netHubs,
    edges
  }
}

async function readLayoutSidecar(
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

function buildMockGraph(): GraphPayload {
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

function buildMockLayout(): LayoutPayload {
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

async function getWebviewHtml(webview: vscode.Webview, extensionUri: vscode.Uri): Promise<string> {
  const mediaUri = vscode.Uri.joinPath(extensionUri, 'media')
  const indexUri = vscode.Uri.joinPath(mediaUri, 'index.html')
  const webviewBase = webview.asWebviewUri(mediaUri).toString()
  const csp = [
    "default-src 'none'",
    `img-src ${webview.cspSource} data:`,
    `style-src ${webview.cspSource} 'unsafe-inline'`,
    `script-src ${webview.cspSource}`
  ].join('; ')

  try {
    const raw = await vscode.workspace.fs.readFile(indexUri)
    const html = Buffer.from(raw).toString('utf8')
    return html
      .replace('__BASE__', `${webviewBase}/`)
      .replace('__CSP__', csp)
  } catch (error) {
    return fallbackHtml(webviewBase)
  }
}

function fallbackHtml(webviewBase: string) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ASDL Visualizer</title>
    <style>
      body { font-family: Segoe UI, sans-serif; padding: 24px; }
      code { background: #f0f0f0; padding: 2px 4px; }
    </style>
  </head>
  <body>
    <h1>ASDL Visualizer</h1>
    <p>Webview bundle not found at <code>${webviewBase}</code>.</p>
    <p>Run <code>npm run build</code> in <code>extensions/asdl-visualizer</code>.</p>
  </body>
</html>`
}
