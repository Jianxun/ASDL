import * as vscode from 'vscode'
import YAML from 'yaml'

import { loadVisualizerDump, loadVisualizerModuleList, VisualizerDumpError } from './dumpRunner'
import { buildMockLayout, readLayoutSidecar, writeLayoutSidecar } from './layout'
import { buildGraphFromDump, buildMockGraph } from './symbols'
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
