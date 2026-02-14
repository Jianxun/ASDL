import * as childProcess from 'child_process'
import * as fs from 'fs'
import * as path from 'path'
import * as readline from 'readline'

export interface WorkerCompletionItem {
  label: string
  kind: string
  insert_text: string
  detail: string
  sort_text: string
}

interface WorkerResponse {
  id: number | null
  ok: boolean
  result?: unknown
  error?: {
    code?: string
    message?: string
  }
}

interface PendingRequest {
  resolve: (value: unknown) => void
  reject: (reason: Error) => void
  timeout: NodeJS.Timeout
}

export interface WorkerClientOptions {
  workerPath?: string
  pythonCommand?: string
  requestTimeoutMs?: number
  workspaceRoots?: string[]
  libRoots?: string[]
  configPath?: string
}

export interface WorkerProtocolClient {
  initialize(): Promise<void>
  updateDocument(uri: string, version: number, text: string): Promise<void>
  complete(uri: string, line: number, character: number): Promise<WorkerCompletionItem[]>
  shutdown(): Promise<void>
}

const DEFAULT_TIMEOUT_MS = 1500

/**
 * JSON-over-stdio client for the ASDL Python completion worker.
 */
export class WorkerClient implements WorkerProtocolClient {
  private readonly workerPath: string
  private readonly pythonCommand: string
  private readonly requestTimeoutMs: number
  private readonly workspaceRoots: string[]
  private readonly libRoots: string[]
  private readonly configPath?: string

  private process: childProcess.ChildProcessWithoutNullStreams | null = null
  private lineReader: readline.Interface | null = null
  private nextRequestId = 1
  private readonly pending = new Map<number, PendingRequest>()

  constructor(options: WorkerClientOptions = {}) {
    this.workerPath = options.workerPath ?? defaultWorkerPath()
    this.pythonCommand = options.pythonCommand ?? process.env.ASDL_PYTHON ?? ''
    this.requestTimeoutMs = options.requestTimeoutMs ?? DEFAULT_TIMEOUT_MS
    this.workspaceRoots = options.workspaceRoots ?? []
    this.libRoots = options.libRoots ?? []
    this.configPath = options.configPath
  }

  async initialize(): Promise<void> {
    this.ensureStarted()
    await this.sendRequest('initialize', {
      workspace_roots: this.workspaceRoots,
      lib_roots: this.libRoots,
      config_path: this.configPath,
    })
  }

  async updateDocument(uri: string, version: number, text: string): Promise<void> {
    await this.sendRequest('update_document', {
      uri,
      version,
      text,
    })
  }

  async complete(uri: string, line: number, character: number): Promise<WorkerCompletionItem[]> {
    const result = await this.sendRequest('complete', {
      uri,
      line,
      character,
    })
    const payload = result as { items?: WorkerCompletionItem[] }
    return Array.isArray(payload.items) ? payload.items : []
  }

  async shutdown(): Promise<void> {
    if (!this.process) {
      return
    }
    try {
      await this.sendRequest('shutdown', {})
    } catch {
      // Ignore shutdown failures; process teardown proceeds below.
    }
    this.disposeProcess()
  }

  private ensureStarted(): void {
    if (this.process) {
      return
    }
    if (!fs.existsSync(this.workerPath)) {
      throw new Error(`Completion worker not found: ${this.workerPath}`)
    }

    const repoRoot = path.resolve(path.dirname(this.workerPath), '..', '..', '..')
    const repoSrc = path.join(repoRoot, 'src')
    const env = { ...process.env }
    env.PYTHONPATH = mergePythonPath(env.PYTHONPATH, [repoSrc])
    const pythonCommand = this.pythonCommand || defaultPythonCommand(repoRoot)

    this.process = childProcess.spawn(pythonCommand, [this.workerPath], {
      cwd: repoRoot,
      env,
      stdio: 'pipe',
    })

    this.process.on('error', (error) => {
      this.rejectAllPending(new Error(`Worker process error: ${error.message}`))
      this.disposeProcess()
    })

    this.process.on('exit', (code, signal) => {
      const reason = signal ? `signal ${signal}` : `code ${String(code)}`
      this.rejectAllPending(new Error(`Worker exited with ${reason}`))
      this.disposeProcess()
    })

    this.lineReader = readline.createInterface({ input: this.process.stdout })
    this.lineReader.on('line', (line) => this.handleResponseLine(line))
  }

  private async sendRequest(method: string, params: Record<string, unknown>): Promise<unknown> {
    this.ensureStarted()
    if (!this.process) {
      throw new Error('Worker process is not running')
    }

    const requestId = this.nextRequestId
    this.nextRequestId += 1

    const payload = {
      id: requestId,
      method,
      params,
    }

    const requestPromise = new Promise<unknown>((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pending.delete(requestId)
        reject(new Error(`Worker request timed out: ${method}`))
      }, this.requestTimeoutMs)
      this.pending.set(requestId, {
        resolve,
        reject,
        timeout,
      })
    })

    try {
      this.process.stdin.write(`${JSON.stringify(payload)}\n`)
    } catch (error) {
      const pending = this.pending.get(requestId)
      if (pending) {
        clearTimeout(pending.timeout)
        this.pending.delete(requestId)
      }
      throw new Error(`Failed to write request to worker: ${(error as Error).message}`)
    }

    return requestPromise
  }

  private handleResponseLine(line: string): void {
    if (!line.trim()) {
      return
    }

    let response: WorkerResponse
    try {
      response = JSON.parse(line) as WorkerResponse
    } catch {
      this.rejectAllPending(new Error('Worker emitted invalid JSON response'))
      return
    }

    if (typeof response.id !== 'number') {
      return
    }

    const pending = this.pending.get(response.id)
    if (!pending) {
      return
    }
    clearTimeout(pending.timeout)
    this.pending.delete(response.id)

    if (response.ok) {
      pending.resolve(response.result)
      return
    }

    const errorMessage = response.error?.message ?? 'Unknown worker error'
    pending.reject(new Error(errorMessage))
  }

  private rejectAllPending(error: Error): void {
    for (const [requestId, pending] of this.pending.entries()) {
      clearTimeout(pending.timeout)
      this.pending.delete(requestId)
      pending.reject(error)
    }
  }

  private disposeProcess(): void {
    if (this.lineReader) {
      this.lineReader.removeAllListeners()
      this.lineReader.close()
      this.lineReader = null
    }
    if (this.process) {
      this.process.removeAllListeners()
      if (!this.process.killed) {
        this.process.kill()
      }
      this.process = null
    }
  }
}

function defaultWorkerPath(): string {
  return path.resolve(__dirname, '..', '..', 'python', 'worker.py')
}

function defaultPythonCommand(repoRoot: string): string {
  const venvPython = path.join(repoRoot, 'venv', 'bin', 'python')
  if (fs.existsSync(venvPython)) {
    return venvPython
  }
  return 'python3'
}

function mergePythonPath(existing: string | undefined, entries: string[]): string {
  const delimiter = process.platform === 'win32' ? ';' : ':'
  const filtered = entries.filter((entry) => entry.length > 0)
  if (!existing) {
    return filtered.join(delimiter)
  }
  return [...filtered, existing].join(delimiter)
}
