# ASDL CLI (asdlc) – Todo Tracker

Reference: `ASDL/context/cli_implementation_plan.md`

Legend: `[ ]` pending, `[x]` done

## Global Conventions
- [ ] Follow ASDL/development-guidelines TDD: write one test file → run (fail) → implement minimal code → run (pass) → refactor → proceed
- [x] Keep branch scope single-purpose (CLI only) and follow conventional commits
- [ ] Update `ASDL/context/memory.md` and this file after milestones

---

## Phase A (MVP)
Focus: Implement core subcommands, JSON diagnostics, exit codes, packaging entries, and initial tests.

### A1. CLI Skeleton & Entry Points
- [x] Create CLI group with `click.Group` named `cli` (refactored into package `src/asdl/cli/`)
- [x] Implement subcommands scaffolds with `--help`:
  - [x] `version`
  - [x] `diag-codes`
  - [x] `validate`
  - [x] `elaborate`
  - [x] `netlist`
- [x] Wire `pyproject.toml` `[project.scripts]`:
  - [x] `asdlc = "asdl.cli:cli"`
  - [x] Optional alias: `asdl = "asdl.cli:cli"`

### A2. Pipeline Integration
- [x] Reuse modules and plumb parameters:
  - [x] Parser: `ASDLParser.parse_file`
  - [x] Elaborator: `Elaborator.elaborate`
  - [x] Validator: `ASDLValidator`
  - [x] Generator: `SPICEGenerator.generate`
- [x] Implement I/O and options:
  - [x] Shared `input.yml` argument handling
  - [x] `-o/--output` where applicable
  - [x] `--top` (optional override; no-op if not provided)
- [x] Diagnostics aggregation across stages (parser/elab/validator)
- [x] Human-readable diagnostics printing (default)
- [x] JSON output when `--json` flag set (match schema in plan)
- [x] Exit code policy: 0 (ok), 1 (ERROR or WARNING under strict later), 2 (usage), 3 (unexpected failure)

### A3. `netlist` Command (MVP behavior)
- [x] End-to-end: parse → elaborate → validate → generate SPICE
- [x] Default output path (input stem + `.spice`) when `-o` not provided
- [x] Create output directories as needed

### A4. `elaborate` Command (MVP behavior)
- [x] Parse → elaborate and emit structure
- [x] Output format option: `--format {yaml,json}`

### A5. `validate` Command (MVP behavior)
- [x] Parse → (elaborate if needed) → validate
- [x] Human text diagnostics; support `--json`

### A6. `diag-codes` and `version`
- [x] Print known diagnostic code prefixes (stub)
- [x] Print semantic version and environment info

### A7. Tests (unit) — under `ASDL/tests/cli/`
- [ ] `test_version.py`
  - [ ] Write test (expect version string)
  - [ ] Run to see failure
  - [ ] Implement
  - [ ] Run to pass
- [ ] `test_netlist_basic.py`
  - [ ] Write test (simple fixture → `.spice` exists and contains `.subckt`)
  - [ ] Run to see failure
  - [ ] Implement
  - [ ] Run to pass
- [ ] `test_elaborate_basic.py`
  - [ ] Write test (emits elaborated YAML/JSON; sanity keys)
  - [ ] Run to see failure
  - [ ] Implement
  - [ ] Run to pass
- [ ] `test_validate_ok.py`
  - [ ] Write test (clean fixture → exit 0, no ERROR)
  - [ ] Run to see failure
  - [ ] Implement
  - [ ] Run to pass
- [ ] `test_validate_error.py`
  - [ ] Write test (malformed fixture → exit 1; captures code/location)
  - [ ] Run to see failure
  - [ ] Implement
  - [ ] Run to pass
- [ ] `test_json_output.py`
  - [ ] Write test (`--json` matches schema; diagnostics array)
  - [ ] Run to see failure
  - [ ] Implement
  - [ ] Run to pass

### A8. Integration Tests
- [ ] Reuse inverter/diff_pair fixtures to validate `asdlc netlist` parity with `scripts/netlist_asdl.py`

### A9. Docs & Help UX
- [ ] Ensure `asdlc --help` and subcommands show options and brief examples
- [ ] Add CLI quickstart stub in `ASDL/docs` (to be expanded in Phase B)

### A10. Acceptance Checklist
- [ ] `asdlc --help` shows all MVP subcommands with options
- [ ] `asdlc netlist tests/fixtures/inverter.yml` produces valid `.spice`
- [ ] `asdlc validate <bad.yml>` exits code 1 and shows diagnostic codes with locations
- [ ] `--json` output conforms to schema with artifact paths
- [ ] CI passes on Linux and macOS with new CLI tests

---

## Phase B (Quality & DX)
Focus: DevX options, streams, deprecation notice, docs.

### B1. Options & Streams
- [ ] Add `--dump-elab PATH` to `netlist`/`elaborate`
- [ ] Implement include paths: `-I/--include PATH` (repeatable)
- [ ] Add `--strict` (warnings → errors affect exit code)
- [ ] Support `@file.yml` shorthand for auto output naming
- [ ] Support stdin (`-`) as input and stdout as output stream modes

### B2. Backward Compatibility
- [ ] Add deprecation note path in `scripts/netlist_asdl.py` when invoked

### B3. Documentation
- [ ] Expand CLI reference docs under `ASDL/docs` (usage, options, examples)
- [ ] Document include-path semantics and absolute-path examples

### B4. Tests (DX)
- [ ] `test_strict_mode.py` (warning → error)
  - [ ] Write test → fail → implement → pass
- [ ] Stream mode tests (stdin/stdout) — may be deferred if infra not ready
- [ ] Include path behavior tests (absolute and multiple `-I`)
- [ ] `--dump-elab` artifact exists and matches format

---

## Phase C (Advanced)
Focus: Lint preset, rule toggles, bindings, graphs, project config.

### C1. Lint Command
- [ ] Add `asdlc lint` dedicated command wired to `ASDLValidator` presets

### C2. Rule Toggles
- [ ] Implement `--rule RULE_ID` and `--disable RULE_ID`
- [ ] Validate rule IDs and error out on unknown IDs

### C3. Binding Overlays (future-ready)
- [ ] Parse and accept `--binding PATH` (repeatable)
- [ ] Validate existence and stage for resolver integration

### C4. Graph Exports
- [ ] `--emit graph.dot/json` for module graphs

### C5. Project Config
- [ ] Support `asdlc.yaml` with include paths and defaults
- [ ] Precedence rules: CLI flags > project config > defaults

---

## Cross-Cutting & Quality
- [ ] Verbose mode (`-v`) with step headings and small metrics
- [ ] Colorized output gated by TTY detection (optional)
- [ ] Consistent diagnostics UX in human vs JSON modes
- [ ] Performance sanity (no excessive overhead)
- [ ] Risk tracking:
  - [ ] Document `ruamel.yaml` inline map pattern limitation and workaround
  - [ ] Test include-path semantics across environments

---

## Tracking & Housekeeping
- [ ] Keep this checklist updated with `[x]` as items complete
- [ ] Move finished items to a "Completed" section if it grows too long
- [ ] After each phase:
  - [ ] Ensure all tests green
  - [ ] Update `ASDL/context/memory.md` with decisions and state
  - [ ] Tag and document milestones
