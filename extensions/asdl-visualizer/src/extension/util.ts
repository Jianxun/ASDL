import path from 'path'
import * as vscode from 'vscode'

type AsdlResolution = {
  uri: vscode.Uri | null
  error?: string
}

export async function resolveActiveAsdlUri(): Promise<AsdlResolution> {
  const editor = vscode.window.activeTextEditor
  if (!editor) {
    return {
      uri: null,
      error: 'Open an .asdl or .sch.yaml file before launching the visualizer.'
    }
  }
  const uri = editor.document.uri
  const filePath = uri.fsPath
  if (filePath.endsWith('.asdl')) {
    return { uri }
  }

  if (filePath.endsWith('.sch.yaml')) {
    const asdlPath = `${filePath.slice(0, -'.sch.yaml'.length)}.asdl`
    const asdlUri = vscode.Uri.file(asdlPath)
    if (await fileExists(asdlUri)) {
      return { uri: asdlUri }
    }
    return {
      uri: null,
      error: `No companion .asdl file found for ${path.basename(filePath)}.`
    }
  }

  return {
    uri: null,
    error: 'Open an .asdl or .sch.yaml file before launching the visualizer.'
  }
}

export async function fileExists(uri: vscode.Uri): Promise<boolean> {
  try {
    await vscode.workspace.fs.stat(uri)
    return true
  } catch {
    return false
  }
}
