import test from 'node:test'
import assert from 'node:assert/strict'

import { CompletionProviderCore, fallbackCompletions } from '../src/completion/provider'
import type { WorkerCompletionItem, WorkerProtocolClient } from '../src/completion/workerClient'

class StubWorkerClient implements WorkerProtocolClient {
  constructor(
    private readonly completions: WorkerCompletionItem[],
    private readonly shouldFail: boolean = false,
  ) {}

  async initialize(): Promise<void> {
    return
  }

  async updateDocument(_uri: string, _version: number, _text: string): Promise<void> {
    if (this.shouldFail) {
      throw new Error('worker unavailable')
    }
  }

  async complete(_uri: string, _line: number, _character: number): Promise<WorkerCompletionItem[]> {
    if (this.shouldFail) {
      throw new Error('worker unavailable')
    }
    return this.completions
  }

  async shutdown(): Promise<void> {
    return
  }
}

function documentFromText(text: string) {
  const lines = text.split(/\r?\n/)
  return {
    uri: 'file:///tmp/test.asdl',
    version: 1,
    getText: () => text,
    lineAt: (line: number) => ({ text: lines[line] ?? '' }),
  }
}

test('CompletionProviderCore maps worker completion items', async () => {
  const provider = new CompletionProviderCore(
    new StubWorkerClient([
      {
        label: 'M1.D',
        kind: 'endpoint',
        insert_text: 'M1.D',
        detail: 'instance endpoint',
        sort_text: 'M1.D',
      },
    ]),
  )

  const items = await provider.provideCompletions(
    documentFromText('modules:\n  top:\n    nets:\n      $OUT:\n        - M1.\n'),
    { line: 4, character: '        - M1.'.length },
  )

  assert.equal(items.length, 1)
  assert.equal(items[0].label, 'M1.D')
  assert.equal(items[0].insertText, 'M1.D')
})

test('CompletionProviderCore falls back when worker is unavailable', async () => {
  const provider = new CompletionProviderCore(new StubWorkerClient([], true))

  const items = await provider.provideCompletions(
    documentFromText('modules:\n  top:\n    instances:\n      X1: lib.dev \n'),
    { line: 3, character: '      X1: lib.dev '.length },
  )

  assert.ok(items.some((item) => item.insertText === 'param='))
})

test('CompletionProviderCore does not fall back when worker returns empty completions', async () => {
  const provider = new CompletionProviderCore(new StubWorkerClient([]))

  const items = await provider.provideCompletions(
    documentFromText('modules:\n  top:\n    instances:\n      X1: lib.dev \n'),
    { line: 3, character: '      X1: lib.dev '.length },
  )

  assert.deepEqual(items, [])
})

test('fallbackCompletions returns endpoint placeholder for endpoint list items', () => {
  const items = fallbackCompletions('modules:\n  top:\n    nets:\n      $OUT:\n        - \n', {
    line: 4,
    character: '        - '.length,
  })

  assert.ok(items.some((item) => item.insertText === 'inst.port'))
})
