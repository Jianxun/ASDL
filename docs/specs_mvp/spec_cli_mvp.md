# Spec - MVP CLI (asdlc netlist) v0

## Purpose
Define the MVP CLI surface for generating backend netlists from ASDL using the
xDSL pipeline. This spec is focused on the `asdlc netlist` command only.

---

## MVP scope
- One command: `asdlc netlist`.
- Input: an entry ASDL file; import resolution may load dependent files.
- Pipeline: uses `src/asdl/ir/pipeline.py` entrypoint and xDSL PassManager.
- Output: backend netlist text written to a file using the backend extension.
- Diagnostics emitted via the shared diagnostic contract.

Non-goals (MVP):
- Additional subcommands (`elaborate`, `validate`, `visualize`).
- Multi-file batch processing.

---

## Command
```
asdlc netlist <file.asdl> [-o <out.ext>] [--verify|--no-verify] [--backend <name>] [--top-as-subckt] [--lib <dir> ...]
```

### Options
- `-o, --output <path>`: output file path.
  - Default: `{asdl_basename}{extension}` in the same directory as the input file.
- `--verify` / `--no-verify`:
  - Default: `--verify`.
  - Controls whether verifier passes run in the pipeline.
- `--backend <name>`:
  - Default: `sim.ngspice`.
  - Backend name from `config/backends.yaml`.
- `--top-as-subckt`:
  - Pass-through to netlist emitter; keeps subckt wrapper for the top module.
- `--lib <dir>`:
  - Repeatable; prepends a library root to the import search order for logical paths.
  - Applied before `ASDL_LIB_PATH`.

---

## Execution flow
1. Resolve the import graph for the entry file (parses files and builds ProgramDB/NameEnv).
2. Run MVP pipeline via `src/asdl/ir/pipeline.py` on the entry document:
   - AST -> NFIR conversion.
   - NFIR -> IFIR pass manager (verify gates based on `--verify`).
3. Emit backend netlist using `emit_netlist`.
4. Write output file when no error diagnostics are present.

## Import resolution (when enabled)
- Logical import paths are resolved by searching:
  1) CLI `--lib` roots (in CLI order)
  2) `ASDL_LIB_PATH` roots (PATH-style list, in order)
- Explicit relative paths (`./` or `../`) resolve against the importing file.

---

## Diagnostics and exit codes
- Diagnostics are printed in deterministic order.
- Exit codes:
  - `0`: success (no error diagnostics).
  - `1`: error diagnostics produced or pipeline/emission returned `None`.
- User-facing failures must be diagnostics, not uncaught exceptions.

---

## Determinism
- The output netlist and diagnostic ordering must be deterministic for identical
  inputs and CLI flags.
