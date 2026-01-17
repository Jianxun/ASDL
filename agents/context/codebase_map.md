# Codebase Map

## Directories
- `src/asdl/`: active refactor code (`ast/`, `diagnostics/`, `ir/`, `cli/`, `emit/`, `imports/`).
- `legacy/`: archived code and tests for reference only.
- `legacy/tests/`: archived pytest suites and fixtures.
- `docs/`: design docs (parser, elaborator, diagnostic system, CLI, schema, logging, xDSL plans, etc.).
- `docs/specs_mvp/`: MVP specs (AST, NFIR, IFIR, netlist emission).
- `examples/`: ASDL libraries and test circuits; includes PDK samples.
- `config/`: configuration files (e.g., `backends.yaml` for backend system devices).
- `prototype/visualizer_react_flow/`: React Flow visualizer MVP.
- `prototype/visualization/`: legacy jsPlumb prototype.
- `agents/context/`: working memory (lessons, contract, tasks, handoff, tasks_archived, codebase_map).
- `agents/roles/`: role briefs (Architect, Executor, Explorer).
- `agents/adr/`: architecture decision records.
- `agents/scratchpads/`: task/idea scratchpads (e.g., `T-030_ast_parser_mvp.md`).
- `docs/specs/`: canonical specs (e.g., `docs/specs/spec_ast.md`, `docs/specs/spec_asdl_cir.md` for v0 AST/IR).
- `scripts/`: helper scripts (e.g., schema generation, visualizer start).
- `syntax-highlighter/`: VSCode extension assets for ASDL syntax.

## Quick Reference: Imports Subsystem
- `src/asdl/imports/`: import resolution package (resolver, program DB, name env, diagnostics).

## Quick Reference: AST
- `src/asdl/ast/schema.py`: JSON/text schema generator helpers for CLI/scripts.

## Quick Reference: GraphIR
- `src/asdl/ir/graphir/attrs.py`: GraphIR attrs and coercion helpers.
- `src/asdl/ir/graphir/ops_program.py`: GraphIR program op.
- `src/asdl/ir/graphir/ops_module.py`: GraphIR module/device ops and port order helpers.
- `src/asdl/ir/graphir/ops_graph.py`: GraphIR net/instance/endpoint ops.
- `src/asdl/ir/graphir/dialect.py`: dialect registry and exports.
- `src/asdl/ir/converters/graphir_to_ast.py`: GraphIR -> AST normalized projection (rebundling lives in projection).

## Quick Reference: IR Pattern Passes
- `src/asdl/ir/patterns/atomization.py`: IFIR pattern atomization pass + rebundling helpers.
- `src/asdl/ir/patterns/elaboration.py`: IFIR pattern elaboration pass for emission.

## Quick Reference: Emission Subsystem
- `src/asdl/emit/netlist/`: netlist emitter package (API, verification, rendering, templates, params, IR helpers, diagnostics)
- `src/asdl/emit/backend_config.py`: backend config loader and system device validation (created in T-047)
- `config/backends.yaml`: backend configuration file with system device templates (created in T-047)
- `tests/unit_tests/emit/`: emission tests (backend config loading, system device validation)
- `tests/unit_tests/netlist/`: netlist emission tests (device instances, module instantiation, end-to-end)
