# Spec - MVP CLI (asdlc netlist) v0

## Purpose
Define the MVP CLI surface for generating backend netlists from ASDL using the
xDSL pipeline. This spec is focused on the `asdlc netlist` command only.

---

## MVP scope
- One command: `asdlc netlist`.
- Input: a single ASDL file parsed into `AsdlDocument`.
- Pipeline: uses `src/asdl/ir/pipeline.py` entrypoint and xDSL PassManager.
- Output: backend netlist text written to a file using the backend extension.
- Diagnostics emitted via the shared diagnostic contract.

Non-goals (MVP):
- Additional subcommands (`elaborate`, `validate`, `visualize`).
- Multi-file batch processing.

---

## Command
```
asdlc netlist <file.asdl> [-o <out.ext>] [--verify|--no-verify] [--backend <name>] [--top-as-subckt]
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

---

## Execution flow
1. Parse input file into `AsdlDocument` (AST validation included).
2. Run MVP pipeline via `src/asdl/ir/pipeline.py`:
   - AST -> NFIR conversion.
   - NFIR -> IFIR pass manager (verify gates based on `--verify`).
3. Emit backend netlist using `emit_netlist`.
4. Write output file when no error diagnostics are present.

## Import resolution (when enabled)
- Library roots include `ASDL_LIB_PATH` (PATH-style list, in order).

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
