# Codebase Map

## Directories
- `src/asdl/`: active refactor code (`ast/`, `diagnostics/`, `ir/`).
- `legacy/`: archived code and tests for reference only.
- `legacy/tests/`: archived pytest suites and fixtures.
- `docs/`: design docs (parser, elaborator, diagnostic system, CLI, schema, logging, xDSL plans, etc.).
- `examples/`: ASDL libraries and test circuits; includes PDK samples.
- `prototype/visualizer_react_flow/`: React Flow visualizer MVP.
- `prototype/visualization/`: legacy jsPlumb prototype.
- `agents/context/`: working memory (lessons, contract, tasks, handoff, tasks_archived, codebase_map).
- `agents/roles/`: role briefs (Architect, Executor, Explorer).
- `agents/adr/`: architecture decision records.
- `agents/scratchpads/`: task/idea scratchpads (e.g., `xDSL_refactor.md`).
- `docs/specs/`: canonical specs (e.g., `docs/specs/spec_ast.md`, `docs/specs/spec_asdl_cir.md` for v0 AST/IR).
- `scripts/`: helper scripts (e.g., schema generation, visualizer start).
