import path from 'path'
import * as vscode from 'vscode'
import YAML from 'yaml'

import { loadVisualizerDump, loadVisualizerModuleList, VisualizerDumpError } from './dumpRunner'
import { buildMockLayout, readLayoutSidecar, writeLayoutSidecar } from './layout'
import { buildGraphFromDump, buildMockGraph, collectFileIds, loadSymbolLibrary } from './symbols'
import type { LoadGraphPayload, VisualizerModule } from './types'
import { resolveActiveAsdlUri } from './util'
import { getWebviewHtml } from './webview'

const VIEW_TYPE = 'asdlVisualizer'

export function registerOpenVisualizerCommand(
  context: vscode.ExtensionContext
): vscode.Disposable {
  return vscode.commands.registerCommand('asdl.openVisualizer', async () => {
    const asdlUri = resolveActiveAsdlUri()
    if (!asdlUri) {
      vscode.window.showErrorMessage('Open an .asdl file before launching the visualizer.')
      return
    }

    let activeModuleName: string | null = null
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

    const postGraphPayload = async (preferredModuleName?: string | null) => {
      try {
        const result = await loadGraphPayload(
          asdlUri,
          panel.webview,
          context.extensionUri,
          preferredModuleName ?? undefined
        )
        activeModuleName = result.moduleName
        panel.webview.postMessage({ type: 'loadGraph', payload: result.payload })
        panel.webview.postMessage({
          type: 'diagnostics',
          payload: { items: result.payload.diagnostics }
        })
      } catch (error) {
        const details = error instanceof Error ? error.message : String(error)
        const diagnostics = error instanceof VisualizerDumpError ? error.diagnostics : []
        const mergedDiagnostics =
          diagnostics.length > 0 ? diagnostics : [`Failed to load visualizer dump: ${details}`]
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

    panel.webview.onDidReceiveMessage(async (message) => {
      if (message?.type === 'ready') {
        await postGraphPayload(activeModuleName)
      }

      if (message?.type === 'reload') {
        const requestedModule =
          typeof message?.payload?.moduleId === 'string' ? message.payload.moduleId : null
        await postGraphPayload(requestedModule ?? activeModuleName)
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
}

async function loadGraphPayload(
  asdlUri: vscode.Uri,
  webview: vscode.Webview,
  extensionUri: vscode.Uri,
  preferredModuleName?: string
): Promise<{ payload: LoadGraphPayload; moduleName: string }> {
  const diagnostics: string[] = []
  const moduleList = await loadVisualizerModuleList(asdlUri)
  diagnostics.push(...moduleList.diagnostics)
  const selectedModule = await resolveModule(moduleList.modules, preferredModuleName)
  const dumpResult = await loadVisualizerDump(asdlUri, selectedModule.name)
  diagnostics.push(...dumpResult.diagnostics)
  configureWebviewRoots(webview, extensionUri, dumpResult.dump)
  const symbolLibrary = await loadSymbolLibrary(dumpResult.dump, webview)
  diagnostics.push(...symbolLibrary.diagnostics)
  const graph = buildGraphFromDump(dumpResult.dump, diagnostics, symbolLibrary.symbols)
  const layout = await readLayoutSidecar(asdlUri, graph, dumpResult.dump.module.name)
  return { payload: { graph, layout, diagnostics }, moduleName: selectedModule.name }
}

function configureWebviewRoots(
  webview: vscode.Webview,
  extensionUri: vscode.Uri,
  dump: Parameters<typeof collectFileIds>[0]
) {
  const roots = new Map<string, vscode.Uri>()
  roots.set(extensionUri.fsPath, extensionUri)
  collectFileIds(dump).forEach((fileId) => {
    if (!fileId) {
      return
    }
    const dir = path.dirname(fileId)
    if (!roots.has(dir)) {
      roots.set(dir, vscode.Uri.file(dir))
    }
  })
  webview.options = {
    enableScripts: true,
    localResourceRoots: Array.from(roots.values())
  }
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

async function resolveModule(
  modules: VisualizerModule[],
  preferredModuleName?: string
): Promise<VisualizerModule> {
  if (preferredModuleName) {
    const match = modules.find((module) => module.name === preferredModuleName)
    if (match) {
      return match
    }
    vscode.window.showWarningMessage(
      `Module "${preferredModuleName}" is no longer available. Select another module.`
    )
  }
  return promptForModule(modules)
}
