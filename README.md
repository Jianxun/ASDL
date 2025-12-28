# ASDL — Analog Structured Description Language

An intermediate representation and toolchain for analog circuits. ASDL bridges human-friendly schematics and machine-friendly netlists, with a CLI (`asdlc`) that compiles designs end‑to‑end and an interactive schematic visualizer.

## Overview

ASDL is a YAML-based format and Python toolkit for describing analog circuits with hierarchy and design intent. The toolchain parses, elaborates, validates, and generates SPICE netlists, and can export interactive schematic graphs for visualization.

### Big‑picture capabilities (asdlc)
- Parse ASDL with precise location tracking
- Resolve imports via `ASDL_PATH` (aliasing, cycle detection)
- Elaborate designs: pattern expansion, parameter resolution, environment variables (`${VAR}`)
- Validate with structured diagnostics (file:line:column)
- Generate LVS‑friendly SPICE netlists
- Export schematic JSON and launch a React Flow visualizer with position persistence
- Structured logging: `-v`, `--debug`, `--trace`, `--log-file`; env overrides

## Quick Start

### 1) Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set environment variables (paths tailored to your setup):
```bash
export ASDL_PATH=examples/libs:examples/libs_common
export PDK_ROOT=examples/pdks/gf180mcu
```
Tip: see `examples/setup.sh` for a ready-made setup snippet.

### 2) Typical CLI usage
```bash
# Elaborate and validate (prints diagnostics and summary)
asdlc elaborate examples/libs/ota_single_ended/tb/tb_ota_5t.asdl --debug

# Generate SPICE netlist (writes .spice next to the source by default)
asdlc netlist   examples/libs/ota_single_ended/tb/tb_ota_5t.asdl

# Visualize a module as an interactive schematic
asdlc visualize examples/libs/ota_single_ended/tb/tb_ota_5t.asdl --module tb_ota_5t
```

## CLI commands
- `asdlc elaborate <file.asdl> [--module <name>] [--debug|--trace]`
  - Parses, resolves imports via `ASDL_PATH`, expands patterns, resolves parameters and environment variables, and validates the design.

- `asdlc netlist <file.asdl> [--module <name>]`
  - Generates an LVS-friendly SPICE netlist for the selected module.

- `asdlc visualize <file.asdl> [--module <name>]`
  - Exports `{basename}.{module}.sch.json` alongside the `.asdl` file and launches a React Flow visualizer. Existing node positions are reused.

## Project structure
```
ASDL/
├── context/                           # Project context: status, todos, decisions
├── doc/                               # Design docs (diagnostics, elaborator, schema, CLI)
├── examples/                          # Example ASDL designs and PDK stubs
├── prototype/
│   └── visualizer_react_flow/         # React Flow visualizer app
├── scripts/                           # Utility scripts
├── src/asdl/                          # Main source code (installed as 'asdl')
│   ├── cli/                           # CLI entrypoints and orchestration
│   ├── parser/                        # Parsing, file info, error reporting
│   ├── elaborator/                    # Pattern/param/env-var resolution, import system
│   ├── validator/                     # Modular validation rules and runner
│   ├── generator/                     # SPICE netlist generation
│   ├── data_structures/               # Core types and enums
│   └── logging_utils.py               # Structured logging helpers
├── tests/                             # Unit and integration tests
├── pyproject.toml                     # Packaging and tooling config (defines 'asdlc')
└── requirements.txt                   # Python dependencies
```

## Visualizer
- CLI: `asdlc visualize <file.asdl> [--module <name>]`
- Output: `{basename}.{module}.sch.json` saved next to the source `.asdl`
- Frontend: React Flow with grid/minimap/controls and Manhattan routing
- Nodes: transistors (NMOS/PMOS), ports, generic instances, resistors, capacitors
- Positions are grid‑quantized and persisted across sessions (if a previous JSON exists)

## Testing & Development
```bash
pytest tests/                # Run tests
```

Guidelines
- Use the project virtual environment (`venv/`) for all commands
- PEP 8 style; type hints encouraged
- Logging controlled by CLI flags or env vars (`ASDL_LOG_LEVEL`, `ASDL_LOG_FILE`, `ASDL_LOG_FORMAT`)

## Contributing
1. Fork the repository and create a feature branch
2. Write tests first (TDD), then implement functionality
3. Update docs and context files under `context/`
4. Submit a pull request with a clear description

## License

MIT License (see `pyproject.toml` classifiers)

## Contact

[Add contact information]