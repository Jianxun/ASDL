import { execFile } from 'child_process'
import path from 'path'
import { promisify } from 'util'
import * as vscode from 'vscode'

import type { VisualizerDump, VisualizerModule, VisualizerModuleList } from './types'

const execFileAsync = promisify(execFile)

export class VisualizerDumpError extends Error {
  diagnostics: string[]

  constructor(message: string, diagnostics: string[] = []) {
    super(message)
    this.name = 'VisualizerDumpError'
    this.diagnostics = diagnostics
  }
}

export async function loadVisualizerModuleList(
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

export async function loadVisualizerDump(
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
