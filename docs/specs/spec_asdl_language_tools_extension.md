# Spec - ASDL Language Tools Extension (asdl-language-tools) v1

## Purpose
Define a fresh VS Code/Cursor extension for ASDL authoring ergonomics:
- syntax highlighting
- authoring-time completion

This extension is implemented under `extensions/asdl-language-tools/` and is
independent from prior legacy extension packages.

---

## Scope (v1)
- VS Code/Cursor extension host implementation.
- TextMate-based ASDL syntax highlighting for current net-first authoring syntax.
- Semantic completion for:
  - legal endpoints (`instance.port`)
  - imported symbols (`lib.module` / `lib.device`)
  - inline parameter keys (`param=`)
- Shared completion semantics with ASDL compiler internals via Python reuse.

Non-goals (v1):
- Full LSP implementation.
- Refactoring/rename/code-action support.
- Compiler-equivalent on-type validation and fix-its.

---

## Fresh extension requirement
- Do not import or runtime-depend on legacy extension code.
- New package root is `extensions/asdl-language-tools/`.
- Legacy extension may coexist temporarily but is not a dependency.

---

## User-facing behavior

### Syntax highlighting
The extension MUST highlight:
- top-level keys: `top`, `imports`, `modules`, `devices`
- module blocks: `instances`, `nets`, `patterns`, `instance_defaults`, `exports`, `variables`
- device/backend blocks: `ports`, `parameters`, `variables`, `backends`, `template`
- pattern tokens: `<...>`, `<@name>`, `*`
- endpoint-like tokens: `inst.port`, optional `!` prefix, `$` net names

Highlighting MUST remain YAML-compatible and avoid breaking generic YAML parsing/editing behavior.

### Completion
The extension MUST provide context-aware completion in `.asdl` files:

1. Endpoint completion
- In endpoint contexts (for example `nets` endpoint lists), suggest `instance.port` pairs.
- Port candidates come from legal ports of the resolved instance target (module/device).

2. Imported symbol completion
- In inline instance head contexts, suggest `lib.symbol` candidates from imported namespaces.
- Namespace import discovery follows ASDL import resolution precedence.

3. Parameter completion
- After instance type token, suggest parameter keys as `param=` snippets.
- Parameter candidates derive from resolved target declarations.

Fallback: when semantic resolution is unavailable, return structural/snippet suggestions rather than failing completion.

---

## Architecture

### Host/frontend
- TypeScript VS Code extension (`extensions/asdl-language-tools/src/extension.ts`).
- Registers:
  - language contributions and grammar
  - completion provider
  - optional diagnostics/status surface for worker health

### Backend/semantic engine
- Long-lived Python worker process (stdio JSON protocol).
- Worker reuses ASDL internals:
  - `.asdlrc` config discovery/loading (`src/asdl/cli/config.py`)
  - AST parser/models (`src/asdl/ast/parser.py`, `src/asdl/ast/models.py`)
  - import/name resolution (`src/asdl/imports/*`)
  - diagnostics model (`src/asdl/diagnostics/*`)

Rationale: avoid CLI subprocess per completion request while maximizing semantic reuse and minimizing drift.

---

## Worker protocol (v1)
Transport: newline-delimited JSON messages over stdio.

Requests:
- `initialize`
  - payload: workspace roots, optional env/config overrides
- `update_document`
  - payload: `uri`, `version`, full text snapshot
- `complete`
  - payload: `uri`, cursor position, trigger character/kind
- `shutdown`

Response for `complete`:
- `items`: list of completion entries with fields:
  - `label`, `kind`, `insert_text`, `detail`, `sort_text`
  - optional edit ranges / additional edits
- optional `diagnostics`: advisory, non-blocking diagnostics
- optional `stats`: timing/cache metadata for debug logging

Error handling:
- Worker errors must be structured and non-fatal to the extension process.
- Extension falls back to structural completion when worker is unavailable.

---

## Resolution semantics
- `.asdlrc` discovery and environment interpolation must match CLI behavior.
- Import roots precedence for semantic indexing must match project rules:
  1) invocation/lib overrides
  2) `.asdlrc` `lib_roots`
  3) `ASDL_LIB_PATH`
- Completion resolution must be deterministic for identical workspace state.

---

## Performance and caching
- One worker process per extension host window/workspace.
- Cache parsed/imported files by normalized path + content hash/mtime.
- Target interactive latency:
  - warm completion p95 < 100 ms
  - cold completion p95 < 300 ms on representative library files

---

## Packaging and layout
Planned extension layout:
- `extensions/asdl-language-tools/package.json`
- `extensions/asdl-language-tools/tsconfig.json`
- `extensions/asdl-language-tools/src/extension.ts`
- `extensions/asdl-language-tools/src/completion/*.ts`
- `extensions/asdl-language-tools/syntaxes/asdl.tmLanguage.json`
- `extensions/asdl-language-tools/snippets/asdl.json`
- `extensions/asdl-language-tools/python/worker.py`

---

## Testing and acceptance

### Unit tests
- Python completion engine:
  - endpoint suggestions from resolved instance targets
  - imported namespace symbol suggestions
  - parameter key suggestions (`param=`)

### Integration tests
- Worker protocol lifecycle (`initialize`, `update_document`, `complete`, `shutdown`).
- Cache invalidation when imported files change.
- Fallback behavior when worker crashes/unavailable.

### Extension smoke tests
- `.asdl` files in `examples/` provide expected highlighting and completion categories.
- No runtime dependency on removed legacy extension packages.

Acceptance criteria:
- All three completion categories work on real project examples.
- Highlighting covers net-first spec keys/tokens.
- Semantic completion behavior is aligned with reused ASDL parser/import logic.

---

## Rollout notes
- v1 ships as a new extension package under `extensions/`.
- Legacy syntax-only extension can be deprecated after v1 parity confirmation.
