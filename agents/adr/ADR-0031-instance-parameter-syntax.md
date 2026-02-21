# ADR-0031: Instance Parameter Syntax Supports Quoted Inline and Structured `parameters`

- Status: Accepted
- Date: 2026-02-21

## Context
Instance expressions are currently authored as inline strings using shorthand
`<ref> key=value ...`. Current parsing splits on whitespace, which breaks
parameter values that must preserve spaces (for example simulator directives
such as `.TRAN 0 10u` passed through a `code` device).

We need:
- a backward-compatible fix for inline shorthand with space-containing values
- a durable schema for unambiguous parameter payloads, including multiline/raw text
- consistency with existing naming (`parameters`) already used by devices/backends

## Decision
Adopt dual instance authoring forms:

1. Inline shorthand (backward compatible), now quote-aware:
   - `inst: "code cmd='.TRAN 0 10u'"`
   - parser tokenization must honor quoting instead of raw whitespace splitting

2. Structured instance object (new canonical schema):
   - `inst: {ref: code, parameters: {cmd: ".TRAN 0 10u"}}`
   - multiline values are allowed through YAML scalar forms
   - `parameters` is canonical; `params` is rejected in structured instances

Normalization behavior:
- internal lowering/emission receives the same `(ref, parameters)` semantic payload
  regardless of authoring form.

## Consequences
- Positive: preserves legacy authoring while unblocking pass-through values with spaces.
- Positive: structured form enables safer and clearer authoring for complex payloads.
- Tradeoff: parser/lowering/helpers must support two input forms and shared normalization.

## Alternatives
- Keep whitespace tokenization and require escaping conventions: rejected because it
  remains fragile and user-hostile.
- Replace inline syntax entirely with structured-only: rejected due to avoidable
  migration churn for existing ASDL files.
