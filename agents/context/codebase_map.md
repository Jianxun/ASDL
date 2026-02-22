# Codebase Map

## Directories
- `src/asdl/`: active refactor code (`ast/`, `core/`, `diagnostics/`, `cli/`, `emit/`, `imports/`, `lowering/`, `patterns_refactor/`).
- `legacy/`: archived code and tests for reference only.
- `legacy/tests/`: archived pytest suites and fixtures.
- `docs/`: design docs (parser, elaborator, diagnostic system, CLI, schema, logging, xDSL plans, etc.).
- `docs/legacy/`: decommissioned xDSL-era specs and pipeline docs (GraphIR/IFIR/NFIR).
- `docs/specs_mvp/`: MVP specs (AST, NFIR, IFIR, netlist emission).
- `examples/`: ASDL libraries and test circuits; includes PDK samples.
- `config/`: configuration files (e.g., `backends.yaml` for backend system devices).
- `prototype/visualizer_react_flow/`: React Flow visualizer MVP.
- `prototype/visualization/`: legacy jsPlumb prototype.
- `agents/context/`: working memory (lessons, contract, tasks, handoff, tasks_archived, codebase_map).
- `agents/roles/`: role briefs (Architect, Executor, Explorer).
- `agents/adr/`: architecture decision records.
- `agents/scratchpads/`: task/idea scratchpads (e.g., `T-030_ast_parser_mvp.md`).
- `docs/specs/`: active specs (e.g., `docs/specs/spec_ast.md`, `docs/specs/spec_netlist_ir.md`).
- `scripts/`: helper scripts (e.g., schema generation, visualizer start).
- `extensions/asdl-language-tools/`: VSCode/Cursor ASDL authoring extension (syntax + completion, fresh codebase).
- `extensions/asdl-visualizer/`: VSCode webview visualizer extension (Phase A scaffold).

## Quick Reference: Imports Subsystem
- `src/asdl/imports/`: import resolution package (resolver, program DB, name env, diagnostics).

## Quick Reference: Lowering
- `src/asdl/lowering/`: refactor pipeline lowerers (e.g., AST -> PatternedGraph).

## Quick Reference: AST
- `src/asdl/ast/schema.py`: JSON/text schema generator helpers for CLI/scripts.

## Quick Reference: Legacy GraphIR
- `legacy/src/asdl/ir/graphir/attrs.py`: GraphIR attrs and coercion helpers.
- `legacy/src/asdl/ir/graphir/ops_program.py`: GraphIR program op.
- `legacy/src/asdl/ir/graphir/ops_module.py`: GraphIR module/device ops and port order helpers.
- `legacy/src/asdl/ir/graphir/ops_graph.py`: GraphIR net/instance/endpoint ops.
- `legacy/src/asdl/ir/graphir/dialect.py`: dialect registry and exports.
- `legacy/src/asdl/ir/converters/graphir_to_ast.py`: GraphIR -> AST normalized projection (rebundling lives in projection).

## Quick Reference: Legacy IR Pattern Passes
- `legacy/src/asdl/ir/patterns/atomization.py`: IFIR pattern atomization pass + rebundling helpers.
- `legacy/src/asdl/ir/patterns/elaboration.py`: IFIR pattern elaboration pass for emission.

## Quick Reference: Emission Subsystem
- `src/asdl/emit/netlist/`: netlist emitter package (API, verification, rendering, templates, params, IR helpers, diagnostics)
- `src/asdl/emit/backend_config.py`: backend config loader and system device validation (created in T-047)
- `config/backends.yaml`: backend configuration file with system device templates (created in T-047)
- `tests/unit_tests/emit/`: emission tests (backend config loading, system device validation)
- `tests/unit_tests/netlist/`: netlist emission tests (device instances, module instantiation, end-to-end)

## Quick Reference: View Binding
- `src/asdl/views/models.py`: view config/profile schema validators.
- `src/asdl/views/config.py`: YAML loading + validation diagnostics.
- `src/asdl/views/instance_index.py`: deterministic hierarchy indexing + rule matching scope.
- `src/asdl/views/resolver.py`: baseline + ordered-rule resolution and sidecar entries.
- `src/asdl/views/api.py`: public config/profile APIs and sidecar serialization hooks used by CLI.
- `tests/unit_tests/views/`: unit tests and stable fixtures for view config/index/resolver behavior.
