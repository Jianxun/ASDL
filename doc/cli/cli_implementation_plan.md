# ASDL CLI (asdlc) – Implementation Plan

This document defines the scope, UX, and technical plan for the ASDL command-line interface, named `asdlc` (ASDL compiler). It aligns with `_docs/todo.md` to provide core subcommands for parse/elaborate/validate/netlist and prepares future extensions.

## Goals

- Provide a single, stable CLI entry point for ASDL operations: parse → elaborate → validate → netlist.
- Strong diagnostics UX with machine-readable output and predictable exit codes.
- Backward-compatibility path from `scripts/netlist_asdl.py` to `asdlc netlist`.
- Clean integration with existing modules: `asdl.parser`, `asdl.elaborator`, `asdl.validator`, `asdl.generator`.

## Non-Goals (initial)

- Full project config system and workspace discovery (will come later).
- GUI or web server; this plan is strictly CLI.

## CLI Binary and Entry Point

- Binary name: `asdlc`
- Python entry point: `asdl.cli:cli`
- Packaging: define `asdlc` in `pyproject.toml` `[project.scripts]` (keep `asdl` alias optionally for transition).

## Subcommands (MVP)

1) `asdlc netlist`
- Description: Parse → elaborate → validate → generate SPICE netlist
- Usage:
  - `asdlc netlist input.yml [-o output.spice]`
- Options:
  - `-o, --output PATH` – output SPICE file
  - `--top MODULE` – override top module (if not specified in YAML)
  - `-I, --include PATH` – include/search paths for `!include` and file references (repeatable)
  - `--binding PATH` – device-binding overlay(s) to resolve abstract devices (repeatable; future-ready)
  - `--dump-elab PATH` – write elaborated ASDL (YAML or JSON) for inspection
  - `--json` – emit machine-readable summary to stdout (diagnostics + artifact paths)
  - `-v, --verbose` – verbose progress logs
  - `--strict` – treat warnings as errors
  - `-t, --template` – emit Jinja2 template: skip unresolved placeholder checks; default output suffix `.spice.j2` (when `-o` not provided)

2) `asdlc elaborate`
- Description: Parse → elaborate only; output elaborated ASDL (YAML by default)
- Options: same core I/O flags as `netlist` except generation; `--format {yaml,json}` for output

3) `asdlc validate` (aka linter core)
- Description: Parse → elaborate (if needed) → run `ASDLValidator`; no SPICE output
- Output: human-readable diagnostics or `--json` structure; exit non-zero on errors
- Options:
  - `--rule RULE_ID` / `--disable RULE_ID` – fine-grain rule enable/disable (future-ready)
  - `--strict` – warnings → errors
  - `--json`, `-v`, `-I`, `--binding`, `--top` as above

4) `asdlc render`
- Description: Render a Jinja2 SPICE template (`.j2`) with a YAML/JSON context file
- Usage:
  - `asdlc render my_circuit.spice.j2 --context params.yml [-o my_circuit.spice]`
- Options:
  - `-c, --context PATH` – YAML or JSON context
  - `-o, --output PATH` – explicit output name (default: strip one trailing `.j2`)
  - `-v, --verbose` – verbose logs

5) `asdlc diag-codes`
- Description: Print known diagnostic codes, severities, and short help (from `asdl.diagnostics`)

6) `asdlc version`
- Description: Print version and environment information

## Output & Contracts

- Human text (default) with clear prefixes and location info (already supported by diagnostics).
- Machine output when `--json` is set:
  - Schema (MVP):
    ```json
    {
      "ok": true,
      "stage": "netlist|validate|elaborate",
      "artifacts": {"netlist": "path", "elaborated": "path"},
      "diagnostics": [
        {
          "code": "P102",
          "severity": "ERROR|WARNING|INFO",
          "message": "...",
          "file": "...",
          "line": 12,
          "col": 5
        }
      ]
    }
    ```
- Exit codes:
  - `0`: success, no errors
  - `1`: diagnostics contain ERROR (or WARNING under `--strict`)
  - `2`: CLI usage/config error
  - `3`: unexpected internal failure

## Implementation Details

- Library: Use `click` (already declared in `pyproject.toml`) for composable subcommands and options.
- Module: Create `src/asdl/cli.py` with `cli` as a `click.Group` and subcommands.
- Reuse pipeline:
  - `ASDLParser.parse_file`
  - `Elaborator.elaborate`
  - `ASDLValidator` for validation pass
  - `SPICEGenerator.generate`
- Diagnostics flow:
  - Aggregate diagnostics from parser/elaborator/validator
  - Print human text and/or serialize to JSON
  - Respect `--strict` for exit code evaluation
- I/O conventions:
  - MVP supports explicit file input only (`input.yml`) and optional `-o`.
  - `@file.yml` auto-naming and stdin/stdout stream mode are deferred to Phase B.
  - Create output directories as needed
- Include paths:
  - Maintain a list passed through parser/loader if supported; otherwise pre-resolve includes (MVP may document limitations)
- Binding overlays (future-ready):
  - Accept `--binding` paths; no-op initially unless `resolver` path available; validate existence and stage for later integration

## Packaging Tasks

- Add to `pyproject.toml`:
  - `[project.scripts]`
    - `asdlc = "asdl.cli:cli"`
    - Optional alias during transition: `asdl = "asdl.cli:cli"`
- Keep `scripts/netlist_asdl.py` for now; print deprecation note when invoked (follow-up change).

## Testing Plan

- Unit tests under `ASDL/tests/cli/`:
  - `test_version.py` – `asdlc version` outputs semantic version
  - `test_netlist_basic.py` – netlists simple resistor example; asserts file exists and contains `.subckt`
  - `test_elaborate_basic.py` – emits elaborated YAML/JSON; sanity-check keys
  - `test_validate_ok.py` – clean fixture returns exit 0, no ERROR diagnostics
  - `test_validate_error.py` – malformed fixture returns exit 1; captures code and location
  - `test_json_output.py` – `--json` produces schema with diagnostics array
  - `test_strict_mode.py` – warning becomes error with `--strict`
  - (Defer stdin/stdout tests to Phase B)
- Integration tests:
  - Reuse existing integration fixtures (e.g., inverter, diff_pair) to validate `asdlc netlist` parity with scripts

## UX Details

- Verbose mode includes step headings and small metrics (counts), similar to current script.
- Consistent emoji prefixes acceptable in human mode; suppressed in `--json` mode.
- Colored output (optional future) gated by TTY detection.

## Roadmap (Phased)

- Phase A (MVP)
  - Implement `version`, `diag-codes`, `validate`, `elaborate`, `netlist`
  - JSON diagnostics and exit codes
  - Pyproject script entries (`asdlc`, alias `asdl` optional)
  - Tests and docs

- Phase B (Quality & DX)
  - Add `--dump-elab`, `-I/--include`, `--strict`, plus:
    - `@file.yml` shorthand for auto output naming
    - stdin (`-`) input and stdout output stream mode
  - Deprecation note in `scripts/netlist_asdl.py`
  - CLI reference docs in `ASDL/docs`

- Phase C (Advanced)
  - `lint` dedicated command wired to `ASDLValidator` presets
  - Rule toggles: `--rule/--disable`
  - Binding overlays pipeline (abstract devices → concrete PDK devices)
  - Graph exports: `--emit graph.dot/json` for module graphs
  - Project config file support (`asdlc.yaml`) with include paths and defaults

## Acceptance Criteria

- `asdlc --help` shows all MVP subcommands with options and examples
- `asdlc netlist tests/fixtures/inverter.yml` produces a valid `.spice` matching integration expectations
- `asdlc validate <bad.yml>` exits with code 1 and prints diagnostic codes with locations
- `--json` output conforms to the schema and includes artifact paths
- CI passes with new CLI tests on Linux and macOS runners

## Risks & Mitigations

- `ruamel.yaml` inline pattern parsing bug for `<p,n>` maps
  - Mitigation: document as known limitation; recommend multi-line mapping
- Include path semantics may differ across environments
  - Mitigation: explicit `-I` and absolute path examples; add tests
- Backcompat with `scripts/netlist_asdl.py`
  - Mitigation: parity feature set for `netlist`; deprecation notice; keep for one release

## Examples

```bash
# Netlist to explicit file with verbose logs
asdlc netlist examples/inverter.yml -o build/inverter.spice -v

# Validate and emit JSON diagnostics
asdlc validate examples/inverter.yml --json > diag.json

# Elaborate to JSON and inspect
asdlc elaborate examples/diff_pair_nmos.yml --format json -o build/diff_pair_elab.json

# Show diagnostic codes
asdlc diag-codes

# Template mode: produce a Jinja2 template and render it later
asdlc netlist examples/libs/ota_differential/diff_pair/diff_pair_nin.asdl -t
# default output: examples/.../diff_pair_nin.spice.j2

# Render template with YAML context
asdlc render examples/.../diff_pair_nin.spice.j2 -c examples/.../params.yml -o build/diff_pair_nin.spice
```


