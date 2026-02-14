# ADR-0030: ASDL Language Tools Extension Architecture

- Status: Accepted
- Date: 2026-02-14

## Context
ASDL authoring needs first-class editor ergonomics for syntax highlighting and
semantic completion. Completion targets include endpoint suggestions, imported
namespace symbols, and inline parameter keys. The existing
legacy extension implementation is removed and should not constrain new
architecture.

Two implementation choices were considered:
- invoke `asdlc` CLI query commands per completion request
- build a fresh extension with a long-lived semantic backend process

Per-request CLI spawning would maximize transport reuse but introduces latency,
process churn, and weaker interactive UX.

## Decision
Build a fresh extension under `extensions/asdl-language-tools/` with:
- TypeScript VS Code/Cursor host for language contributions and completion UI
- long-lived Python worker process over stdio JSON for semantic completion
- direct reuse of existing ASDL core modules for parser/import/config/diagnostics
- no runtime dependency on removed legacy extension code

LSP is deferred; this worker protocol is an internal v1 transport.

## Consequences
- Positive: semantic behavior stays aligned with compiler internals and avoids
  drift from reimplementation.
- Positive: interactive completion latency is significantly better than
  subprocess-per-request CLI execution.
- Tradeoff: introduces a dual-runtime extension (TypeScript + Python worker)
  and worker lifecycle management complexity.

## Alternatives
- CLI subprocess per request (`asdlc query-*`): rejected for latency and
  process overhead in keystroke-time completion.
- Pure TypeScript semantic analyzer: rejected due to high drift risk and
  duplicated parser/import semantics.
