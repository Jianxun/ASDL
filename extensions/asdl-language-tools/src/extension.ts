import * as path from 'path'
import * as vscode from 'vscode'

import { CompletionProviderCore } from './completion/provider'
import { WorkerClient } from './completion/workerClient'

let workerClient: WorkerClient | undefined

class VsCodeCompletionProvider implements vscode.CompletionItemProvider {
  constructor(private readonly core: CompletionProviderCore) {}

  async provideCompletionItems(
    document: vscode.TextDocument,
    position: vscode.Position,
  ): Promise<vscode.CompletionItem[]> {
    const items = await this.core.provideCompletions(
      {
        uri: document.uri.toString(),
        version: document.version,
        getText: () => document.getText(),
        lineAt: (line) => document.lineAt(line),
      },
      { line: position.line, character: position.character },
    )

    return items.map((item) => {
      const completion = new vscode.CompletionItem(item.label, toVsCodeCompletionKind(item.kind))
      completion.detail = item.detail
      completion.sortText = item.sortText
      completion.insertText = item.insertText
      return completion
    })
  }
}

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const workspaceRoots = (vscode.workspace.workspaceFolders ?? []).map((folder) => folder.uri.fsPath)

  workerClient = new WorkerClient({
    workerPath: path.join(context.extensionPath, 'python', 'worker.py'),
    workspaceRoots,
  })

  try {
    await workerClient.initialize()
  } catch {
    // Worker startup failures are handled by fallback completions.
  }

  const completionCore = new CompletionProviderCore(workerClient)

  context.subscriptions.push(
    vscode.languages.registerCompletionItemProvider(
      { language: 'asdl', scheme: 'file' },
      new VsCodeCompletionProvider(completionCore),
      '.',
      '=',
      ' ',
    ),
  )

  const syncDocument = async (document: vscode.TextDocument): Promise<void> => {
    if (document.languageId !== 'asdl' || !workerClient) {
      return
    }
    try {
      await workerClient.updateDocument(document.uri.toString(), document.version, document.getText())
    } catch {
      // Keep silent; provider fallback remains available.
    }
  }

  for (const document of vscode.workspace.textDocuments) {
    void syncDocument(document)
  }

  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((document) => {
      void syncDocument(document)
    }),
  )

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((event) => {
      void syncDocument(event.document)
    }),
  )

  context.subscriptions.push({
    dispose: () => {
      if (workerClient) {
        void workerClient.shutdown()
        workerClient = undefined
      }
    },
  })
}

export async function deactivate(): Promise<void> {
  if (workerClient) {
    await workerClient.shutdown()
    workerClient = undefined
  }
}

function toVsCodeCompletionKind(kind: string): vscode.CompletionItemKind {
  switch (kind) {
    case 'endpoint':
      return vscode.CompletionItemKind.Field
    case 'symbol':
      return vscode.CompletionItemKind.Module
    case 'param':
      return vscode.CompletionItemKind.Property
    default:
      return vscode.CompletionItemKind.Snippet
  }
}
