# Codebase Map

## Directories
- `src/asdl/`: main compiler code (parser, elaborator, validator, generator, import system, diagnostics, CLI).
- `tests/`: pytest suites (unit/integration) with fixtures.
- `doc/`: design docs (parser, elaborator, diagnostic system, CLI, schema, logging, xDSL plans, etc.).
- `examples/`: ASDL libraries and test circuits; includes PDK samples.
- `prototype/visualizer_react_flow/`: React Flow visualizer MVP.
- `prototype/visualization/`: legacy jsPlumb prototype.
- `agents/context/`: working memory (lessons, contract, tasks, handoff, tasks_archived, codebase_map).
- `agents/roles/`: role briefs (Architect, Executor, Explorer).
- `agents/adr/`: architecture decision records.
- `agents/scratchpads/`: task/idea scratchpads (e.g., `xDSL_refactor.md`).
- `agents/specs/`: canonical specs (e.g., `spec_ast.md`, `spec_asdl_ir.md` for v0 AST/IR).
- `scripts/`: helper scripts (e.g., schema generation, visualizer start).
- `syntax-highlighter/`: VSCode extension assets for ASDL syntax.
