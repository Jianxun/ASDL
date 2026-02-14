import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

import { WorkerClient } from '../src/completion/workerClient'

async function write(filePath: string, content: string): Promise<void> {
  await fs.mkdir(path.dirname(filePath), { recursive: true })
  await fs.writeFile(filePath, content, 'utf8')
}

test('WorkerClient lifecycle and completion round-trip', async () => {
  const workspace = await fs.mkdtemp(path.join(os.tmpdir(), 'asdl-worker-client-'))
  const filePath = path.join(workspace, 'top.asdl')
  const text = [
    'devices:',
    '  dev:',
    '    ports: [P, N]',
    '    parameters:',
    '      l: 1u',
    '    backends:',
    '      ngspice:',
    '        template: "X{inst} {P} {N}"',
    'modules:',
    '  top:',
    '    instances:',
    '      X1: dev l=1u ',
  ].join('\n') + '\n'
  await write(filePath, text)

  const client = new WorkerClient({
    workerPath: path.resolve(process.cwd(), 'python', 'worker.py'),
    workspaceRoots: [workspace],
    requestTimeoutMs: 5000,
  })

  try {
    const fileUri = pathToFileURL(filePath).toString()
    await client.initialize()
    await client.updateDocument(fileUri, 1, text)
    const completions = await client.complete(fileUri, 11, '      X1: dev l=1u '.length)
    assert.ok(completions.some((item) => item.insert_text === 'l='))
  } finally {
    await client.shutdown()
  }
})

test('WorkerClient reports missing worker path', async () => {
  const client = new WorkerClient({
    workerPath: path.resolve(process.cwd(), 'python', 'does-not-exist.py'),
  })

  await assert.rejects(async () => {
    await client.initialize()
  }, /Completion worker not found/)
})
