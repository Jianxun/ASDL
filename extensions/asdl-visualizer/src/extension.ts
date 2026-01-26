import * as vscode from 'vscode'
import { execFile } from 'child_process'
import path from 'path'
import { promisify } from 'util'
import YAML from 'yaml'

const VIEW_TYPE = 'asdlVisualizer'
const execFileAsync = promisify(execFile)

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
          const payload = await loadGraphPayload(asdlUri)
          panel.webview.postMessage({ type: 'loadGraph', payload })
          panel.webview.postMessage({
            type: 'diagnostics',
            payload: { items: payload.diagnostics }
          })
        } catch (error) {
          const details = error instanceof Error ? error.message : String(error)
          const diagnostics = error instanceof VisualizerDumpError ? error.diagnostics : []
          const mergedDiagnostics =
            diagnostics.length > 0
              ? diagnostics
              : [`Failed to load visualizer dump: ${details}`]
          panel.webview.postMessage({
            type: 'loadGraph',
            payload: {
              graph: buildMockGraph(),
              layout: buildMockLayout(),
              diagnostics: mergedDiagnostics
            }
          })
          panel.webview.postMessage({
            type: 'diagnostics',
            payload: { items: mergedDiagnostics }
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

type VisualizerModule = {
  module_id: string
  name: string
  file_id: string
  ports?: string[]
}

type VisualizerDevice = {
  device_id: string
  name: string
  file_id: string
  ports?: string[]
}

type VisualizerDump = {
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
  }>
  registries?: {
    pattern_expressions?: Record<string, { raw?: string }> | null
  }
  refs?: {
    modules?: VisualizerModule[]
    devices?: VisualizerDevice[]
  }
}

type VisualizerModuleList = {
  schema_version: number
  modules: VisualizerModule[]
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

class VisualizerDumpError extends Error {
  diagnostics: string[]

  constructor(message: string, diagnostics: string[] = []) {
    super(message)
    this.name = 'VisualizerDumpError'
    this.diagnostics = diagnostics
  }
}

async function writeLayoutSidecar(asdlUri: vscode.Uri, layoutYaml: string) {
  const dir = path.dirname(asdlUri.fsPath)
  const base = path.basename(asdlUri.fsPath, '.asdl')
  const outPath = path.join(dir, `${base}.sch.yaml`)
  const outUri = vscode.Uri.file(outPath)
  const payload = layoutYaml.endsWith('\n') ? layoutYaml : `${layoutYaml}\n`
  await vscode.workspace.fs.writeFile(outUri, Buffer.from(payload, 'utf8'))
}

async function loadGraphPayload(asdlUri: vscode.Uri): Promise<LoadGraphPayload> {
  const diagnostics: string[] = []
  const moduleList = await loadVisualizerModuleList(asdlUri)
  diagnostics.push(...moduleList.diagnostics)
  const selectedModule = await promptForModule(moduleList.modules)
  const dumpResult = await loadVisualizerDump(asdlUri, selectedModule.name)
  diagnostics.push(...dumpResult.diagnostics)
  const graph = buildGraphFromDump(dumpResult.dump, diagnostics)
  const layout = await readLayoutSidecar(asdlUri, graph, dumpResult.dump.module.name)
  return { graph, layout, diagnostics }
}

async function fileExists(uri: vscode.Uri): Promise<boolean> {
  try {
    await vscode.workspace.fs.stat(uri)
    return true
  } catch {
    return false
  }
}

async function loadVisualizerModuleList(
  asdlUri: vscode.Uri
): Promise<{ modules: VisualizerModule[]; diagnostics: string[] }> {
  const { stdout, stderr } = await runAsdlc(
    ['visualizer-dump', asdlUri.fsPath, '--list-modules', '--compact'],
    path.dirname(asdlUri.fsPath)
  )
  const diagnostics = parseDiagnostics(stderr)
  let payload: VisualizerModuleList
  try {
    payload = JSON.parse(stdout) as VisualizerModuleList
  } catch (error) {
    throw new VisualizerDumpError(
      'Failed to parse module list output from asdlc.',
      diagnostics
    )
  }
  return { modules: payload.modules ?? [], diagnostics }
}

async function loadVisualizerDump(
  asdlUri: vscode.Uri,
  moduleName: string
): Promise<{ dump: VisualizerDump; diagnostics: string[] }> {
  const { stdout, stderr } = await runAsdlc(
    ['visualizer-dump', asdlUri.fsPath, '--module', moduleName, '--compact'],
    path.dirname(asdlUri.fsPath)
  )
  const diagnostics = parseDiagnostics(stderr)
  let payload: VisualizerDump
  try {
    payload = JSON.parse(stdout) as VisualizerDump
  } catch (error) {
    throw new VisualizerDumpError(
      'Failed to parse visualizer dump output from asdlc.',
      diagnostics
    )
  }
  return { dump: payload, diagnostics }
}

async function promptForModule(
  modules: VisualizerModule[]
): Promise<VisualizerModule> {
  if (modules.length === 0) {
    throw new VisualizerDumpError('No modules found in entry file.')
  }
  if (modules.length === 1) {
    return modules[0]
  }

  const picked = await vscode.window.showQuickPick(
    modules.map((module) => ({
      label: module.name,
      description: module.file_id,
      module
    })),
    { placeHolder: 'Select ASDL module to visualize' }
  )
  if (!picked) {
    return modules[0]
  }
  return picked.module
}

function buildGraphFromDump(
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
  const instances = dump.instances?.map((inst) => {
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

  const netHubs = dump.nets?.map((net) => ({
    id: net.net_id,
    label: resolveExprRaw(net.name_expr_id) || net.net_id
  })) ?? []

  const edges = dump.endpoints?.map((endpoint) => {
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

function parseDiagnostics(stderr: string): string[] {
  if (!stderr) {
    return []
  }
  return stderr
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0)
}

async function runAsdlc(
  args: string[],
  cwd: string
): Promise<{ stdout: string; stderr: string }> {
  try {
    const result = await execFileAsync('asdlc', args, {
      cwd,
      encoding: 'utf8',
      maxBuffer: 10 * 1024 * 1024
    })
    return { stdout: result.stdout, stderr: result.stderr ?? '' }
  } catch (error) {
    const execError = error as NodeJS.ErrnoException & { stderr?: string }
    if (execError.code === 'ENOENT') {
      throw new VisualizerDumpError(
        'The ASDL CLI (asdlc) is not available on PATH. Install ASDL or update your PATH.'
      )
    }
    const stderr = typeof execError.stderr === 'string' ? execError.stderr : ''
    const diagnostics = parseDiagnostics(stderr)
    const detail = diagnostics[0] ?? execError.message ?? 'Unknown error.'
    throw new VisualizerDumpError(`asdlc visualizer-dump failed: ${detail}`, diagnostics)
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
