import * as vscode from 'vscode'
import path from 'path'

export function resolveActiveAsdlUri(): vscode.Uri | null {
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

export async function fileExists(uri: vscode.Uri): Promise<boolean> {
  try {
    await vscode.workspace.fs.stat(uri)
    return true
  } catch {
    return false
  }
}
