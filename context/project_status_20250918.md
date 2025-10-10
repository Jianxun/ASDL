## ASDL Project Status — 2025-09-18

### Executive Summary
- **Scope**: ASDL is a Python framework for analog circuit design covering parsing, elaboration, validation, import resolution, and SPICE netlisting, with a visualizer MVP.
- **Overall**: Core architecture is stable. Unit tests are green; integration tests are reported as passing in `context/todo.md`. Visualizer MVP with React Flow is implemented and integrated with CLI export.
- **Highlights**: Import system modularization with XCCSS diagnostics, environment-variable support, structured logging Phase 1, visualizer schema v2 and CLI wiring.
- **Risks**: A critical issue is recorded regarding unresolved variable references in elaboration (see Known Issues); confirm current status. Some docs/examples still reference legacy `models:`.

### Architecture & Components
- **Unified Module System**: Single `Module` for primitive/hierarchical modules
- **Parser**: Modular, location tracking, XCCSS migration complete
- **Elaborator**: Pattern expansion, environment-variable resolution, diagnostics consolidated under `E` codes
- **Validator**: Modular package `src/asdl/validator/` with rules and runner
- **Import System**: Split into coordinator, dependency graph, reference validator, flattener; `ASDL_PATH`-based search policy
- **Generator**: LVS-oriented SPICE, readability updates (two-space indent)
- **Serialization**: Present; verify removal of obsolete `models` (see issues)
- **CLI**: Commands for elaborate, netlist, visualize; logging flags and structured output
- **Visualizer**: React Flow v12 app; CLI `asdlc visualize` exports `{basename}.{module}.sch.json`

### Recent Progress (2025-09-07 → 2025-09-12)
- Import diagnostics split and validation wiring (E0441–E0448; style E0601/E0602)
- Import system refactor into modular subcomponents with graph export and cycle detection consolidation
- Environment variable resolver integrated into elaboration; `${VAR}` supported in parameters and primitive `spice_template`
- Visualizer MVP scaffolded and iterated: transistor/port nodes, Manhattan routing, assets via Vite
- Visualizer schema v2: generic instance nodes, primitive mapping (nmos/pmos/res/cap), per-pin edges
- CLI visualize UX: default module selection, inline JSON via `?data=`, position persistence, output naming
- Logging Phase 1: hierarchical loggers, human/JSON formatters, env var control, CLI flags (`--debug`, `--trace`, `--log-file`)

### Testing Status
- **Unit Tests**: Reported 136/136 passing; elaborator suite expanded (≈47–54 tests) and green post-XCCSS migration
- **Integration Tests**: Marked as passing in `context/todo.md` (“All integration tests now passing”)
- **Note**: A conflicting note in `context/memory.md` indicates generator/integration failures “pending refactor alignment.” Treat todo status as latest; re-run CI to confirm.

### CLI & Logging
- **Import Search Policy**: CLI no longer accepts `--search-path`; resolution via `ASDL_PATH` (fallback ".")
- **Logging**: Root logger `asdlc.*`; flags map levels (`-v`→INFO). Env overrides: `ASDL_LOG_LEVEL`, `ASDL_LOG_FILE`, `ASDL_LOG_FORMAT`.
- **Visualizer CLI**: Launches dev server, opens browser, prints host only, supports inline data and persistence.

### Visualizer (React Flow) MVP
- **Frontend**: Grid, minimap, controls; step edges; node types for `TransistorNode`, `PortNode`, `InstanceNode`, `ResistorNode`, `CapacitorNode`
- **Schema v2**: Instances include `{ id, type, model, pin_list, position }`; edges for every pin; ports with handle `P`
- **Assets & Rendering**: MOSFETs via SVG assets; styling unified (`#111827`, width 2, rounded caps/joins)
- **Persistence**: Reuse prior positions; grid-quantized placement
- **Output**: `{asdl_filename}.{module_name}.sch.json` alongside source `.asdl`

### Known Issues (from `context/bugs.md`)
- **Critical**: Variable references in instance parameters may not resolve during elaboration, yielding literal names in SPICE. Action: verify against current elaborator (`VariableResolver`) and fix if still reproducible.
- **High**: Legacy `models` field usage in tests causes `AttributeError`. Action: ensure migrations completed in all tests.
- **Medium**: YAML/fixtures still contain `models:` sections; serialization references `models` at `src/asdl/serialization.py:52`. Action: clean up and align schema/docs.
- **Low**: Documentation references to `models:` remain in import/schema/example docs. Action: doc refresh.

### Roadmap (Next 1–2 Weeks)
- Confirm and fix variable parameter resolution in elaboration (if still failing); add unit tests
- Strengthen integration tests for env-var resolution through CLI (`asdl elaborate`, `asdl netlist`)
- Finalize import diagnostics per-code tests; increase coverage for E0441–E0448 and E0601–E0602
- Complete schema/text export updates reflecting `PortType` and current data structures
- Visualizer: refine inspector/toolbar, optional orthogonal custom edge, persistence polish
- Documentation pass: ASDL_PATH usage, examples cleanup, remove `models:` remnants

### Repository & Branch State
- Local branches cleaned; `main` tracks `origin/main`
- Visualizer MVP PR created: [feat(visualizer): React Flow MVP with CLI integration](https://github.com/Jianxun/ASDL/pull/14)

### Environment & Configuration
- **Python**: Use project venv at `venv/` for all commands/tests
- **Paths**: `ASDL_PATH` required for imports; `PDK_ROOT` used in examples
- **Logging**: Controlled via CLI flags and env vars

### References
- `context/memory.md` — current state, decisions, design notes
- `context/todo_*.md` — focused backlogs: imports, CLI, schema, logging, visualizer
- `doc/diagnostic_system/` — XCCSS architecture and codes
- `doc/elaborator_design/` — elaborator design and parameter resolution system
- `prototype/visualizer_react_flow/README.md` — schema v2, run instructions
- `examples/setup.sh` — environment setup (e.g., `ASDL_PATH`, `PDK_ROOT`)

### Quick Start
1) Activate venv and export `ASDL_PATH`/`PDK_ROOT`
2) Run `asdlc visualize <file.asdl> [--module <name>]` to generate and view schematic JSON
3) Run `asdlc netlist <file.asdl>` to produce SPICE; inspect logs with `--debug`/`--trace`

### Open Questions
- Is the elaboration-time variable resolution issue still reproducible on `main`? If not, close the critical bug and add a regression test.
- Do any generator/integration tests still fail on CI? Align `context/memory.md` vs `context/todo.md` statuses.


