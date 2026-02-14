import type { WorkerCompletionItem, WorkerProtocolClient } from './workerClient'

export interface TextDocumentLike {
  uri: string
  version: number
  getText(): string
  lineAt(line: number): { text: string }
}

export interface PositionLike {
  line: number
  character: number
}

export interface CompletionItemLike {
  label: string
  kind: string
  insertText: string
  detail: string
  sortText: string
}

/**
 * Editor-agnostic completion provider that routes requests to the Python worker
 * and falls back to structural/snippet suggestions if the worker is unavailable.
 */
export class CompletionProviderCore {
  constructor(private readonly workerClient: WorkerProtocolClient) {}

  async provideCompletions(document: TextDocumentLike, position: PositionLike): Promise<CompletionItemLike[]> {
    const text = document.getText()
    try {
      await this.workerClient.updateDocument(document.uri, document.version, text)
      const items = await this.workerClient.complete(document.uri, position.line, position.character)
      return mapWorkerItems(items)
    } catch {
      // Worker path failed; use local fallback completions.
    }

    return fallbackCompletions(text, position)
  }
}

export function mapWorkerItems(items: WorkerCompletionItem[]): CompletionItemLike[] {
  return items.map((item) => ({
    label: item.label,
    kind: item.kind,
    insertText: item.insert_text,
    detail: item.detail,
    sortText: item.sort_text,
  }))
}

export function fallbackCompletions(text: string, position: PositionLike): CompletionItemLike[] {
  const lines = text.split(/\r?\n/)
  const lineText = lines[position.line] ?? ''
  const prefix = lineText.slice(0, Math.max(0, Math.min(position.character, lineText.length)))
  const trimmedPrefix = prefix.trim()

  if (isEndpointLine(prefix)) {
    return [
      {
        label: 'inst.port',
        kind: 'endpoint',
        insertText: preserveEndpointPrefix(prefix, 'inst.port'),
        detail: 'fallback endpoint suggestion',
        sortText: 'z.endpoint.inst.port',
      },
    ]
  }

  if (isInstanceMappingLine(prefix)) {
    if (prefix.endsWith(' ') && hasInstanceHead(prefix)) {
      return [
        {
          label: 'param=',
          kind: 'param',
          insertText: 'param=',
          detail: 'fallback parameter key suggestion',
          sortText: 'z.param.param',
        },
      ]
    }

    return [
      {
        label: 'lib.symbol',
        kind: 'symbol',
        insertText: 'lib.symbol',
        detail: 'fallback imported symbol suggestion',
        sortText: 'z.symbol.lib.symbol',
      },
    ]
  }

  const indent = prefix.match(/^\s*/)?.[0] ?? ''
  return [
    {
      label: 'modules:',
      kind: 'snippet',
      insertText: `${indent}modules:\n${indent}  top:\n${indent}    instances:\n${indent}      X1: lib.symbol\n${indent}    nets:\n${indent}      $OUT:\n${indent}        - X1.P`,
      detail: 'fallback YAML-safe structure snippet',
      sortText: 'z.snippet.modules',
    },
  ]
}

function isEndpointLine(prefix: string): boolean {
  return /^\s*-\s*\S*$/.test(prefix)
}

function preserveEndpointPrefix(prefix: string, candidate: string): string {
  const dashIndex = prefix.indexOf('-')
  if (dashIndex < 0) {
    return candidate
  }
  const rhs = prefix.slice(dashIndex + 1).trim()
  if (!rhs) {
    return candidate
  }
  return candidate.startsWith(rhs) ? candidate.slice(rhs.length) : candidate
}

function isInstanceMappingLine(prefix: string): boolean {
  if (!prefix.includes(':')) {
    return false
  }
  return /^\s*[^#\s][^:]*:\s*\S*.*$/.test(prefix)
}

function hasInstanceHead(trimmedPrefix: string): boolean {
  const colonIndex = trimmedPrefix.indexOf(':')
  if (colonIndex < 0) {
    return false
  }
  const value = trimmedPrefix.slice(colonIndex + 1).trim()
  if (!value) {
    return false
  }
  return value.split(/\s+/).length >= 1
}
