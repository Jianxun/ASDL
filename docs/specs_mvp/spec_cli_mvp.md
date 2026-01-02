# Spec - MVP CLI (asdlc netlist) v0

## Purpose
Define the MVP CLI surface for generating ngspice netlists from ASDL using the
xDSL pipeline. This spec is focused on the `asdlc netlist` command only.

---

## MVP scope
- One command: `asdlc netlist`.
- Input: a single ASDL file parsed into `AsdlDocument`.
- Pipeline: uses `src/asdl/ir/pipeline.py` entrypoint and xDSL PassManager.
- Output: ngspice netlist text written to a `.spice` file.
- Diagnostics emitted via the shared diagnostic contract.

Non-goals (MVP):
- Additional subcommands (`elaborate`, `validate`, `visualize`).
- Import search paths or include handling.
- Multi-file batch processing.

---

## Command
```
asdlc netlist <file.asdl> [-o <out.spice>] [--verify|--no-verify] [--top-as-subckt]
```

### Options
- `-o, --output <path>`: output file path.
  - Default: input stem with `.spice` extension in the same directory.
- `--verify` / `--no-verify`:
  - Default: `--verify`.
  - Controls whether verifier passes run in the pipeline.
- `--top-as-subckt`:
  - Pass-through to ngspice emitter; keeps `.subckt` and `.ends` for top module.

---

## Execution flow
1. Parse input file into `AsdlDocument` (AST validation included).
2. Run MVP pipeline via `src/asdl/ir/pipeline.py`:
   - AST -> NFIR conversion.
   - NFIR -> IFIR pass manager (verify gates based on `--verify`).
3. Emit ngspice netlist using `emit_ngspice`.
4. Write output file when no error diagnostics are present.

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
