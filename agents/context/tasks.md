# Tasks

## Active OKR(s)
- See `agents/context/okrs.md`.

## Current Sprint
- None.

## Backlog
- T-035 | Status: Done | Owner: Executor | DoD: Decide how to map NFIR `src`/AST locations into IFIR conversion diagnostics; emit span-aware diagnostics (or document why spans are unavailable) for NFIR->IFIR conversion + emission errors; update unit tests as needed. | Verify: `pytest tests/unit_tests/ir`. | Links: scratchpad `agents/scratchpads/T-035_ifir_diagnostics_spans.md`, PR https://github.com/Jianxun/ASDL/pull/35.
- T-038 | Status: Done | Owner: Executor | DoD: Update netlist template placeholders to use `{ports}` (hard switch; remove `{conns}`); treat `{ports}` as optional; only implicit placeholders are `{name}` and `{ports}` (others are user-controlled). Deprecate `{params}` placeholder and remove reserved-status enforcement; update validation rules/diagnostics and tests (missing `{ports}` allowed; unknown placeholders error). Update CLI help text to list supported placeholders. | Verify: `pytest tests/unit_tests/netlist` and `pytest tests/unit_tests/cli`. | Links: scratchpad `agents/scratchpads/T-038_template_placeholders.md`, PR https://github.com/Jianxun/ASDL/pull/36.
- T-039 | Status: In Progress | Owner: Executor | DoD: Improve `asdlc --help` so the top-level menu lists `netlist` and includes a brief command summary; add a CLI help test that asserts the command list appears. | Verify: `pytest tests/unit_tests/cli`. | Links: scratchpad `agents/scratchpads/T-039_cli_help.md`.
## Execution grouping (recommendation)
- Bundle B: T-038 + T-039 (emitter + CLI help).

## Exploration candidates (informal)
- IFIR diagnostics spans: mapping strategy, edge cases, and test fixtures.
- CLI pipeline UX: command flow, error messaging, and file layout.
- Netlist emission validation: strictness vs warnings; validation stages.
- xDSL pipeline boundaries: pass split/merge opportunities and IR boundaries.
- Codebase map gaps: navigation audit for future Executors.

## Done
- T-041 | Status: Done | Owner: Executor | DoD: Make `DeviceDecl.ports` optional in the AST schema; update validations/converters/tests to accept devices with no ports; confirm emission behavior for portless devices. | Verify: `pytest tests/unit_tests/ast` and `pytest tests/unit_tests/ir`. | Links: scratchpad `agents/scratchpads/T-041_device_ports_optional.md`, PR https://github.com/Jianxun/ASDL/pull/34.
- T-043 | Status: Done | Owner: Executor | DoD: Implement list-only endpoint authoring (disallow string endpoint lists) per ADR-0005; update AST schema, parser validation, and converters; update diagnostics to guide users; adjust tests. | Verify: `pytest tests/unit_tests/parser` and `pytest tests/unit_tests/ir`. | Links: scratchpad `agents/scratchpads/T-043_endpoint_list_lists_only.md`, PR https://github.com/Jianxun/ASDL/pull/32.
- T-037 | Status: Done | Owner: Executor | DoD: Update PARSE-003 diagnostics after list-only endpoint authoring lands (T-043). Ensure errors explicitly say endpoint lists must be YAML lists of `<instance>.<pin>` strings; keep instance expr hints for `<model> key=value ...`. Add parser tests for the improved message/notes. | Verify: `pytest tests/unit_tests/parser`. | Links: scratchpad `agents/scratchpads/T-037_parser_endpoint_hints.md`, PR https://github.com/Jianxun/ASDL/pull/33.
- T-036 | Status: Done | Owner: Executor | DoD: Implement CLI command under `src/asdl/cli/` that runs the MVP pipeline end-to-end via `src/asdl/ir/pipeline.py` and emits ngspice output (no direct converter calls); expose `--verify` toggle, deterministic diagnostics, and default output `{asdl_basename}.spice`; add CLI-level tests. Blocked on T-034 completion. | Verify: `pytest tests/unit_tests/cli`. | Links: scratchpad `agents/scratchpads/T-036_cli_pipeline.md`, PR https://github.com/Jianxun/ASDL/pull/31.
- T-045 | Status: Done | Owner: Architect | DoD: Update AST specs (`docs/specs_mvp/spec_ast_mvp.md`, `docs/specs/spec_ast.md`) to make `DeviceDecl.ports` optional and reflect list-only endpoint lists per ADR-0005. | Verify: none (doc task). | Links: scratchpad `agents/scratchpads/T-045_ast_specs_updates.md`.
