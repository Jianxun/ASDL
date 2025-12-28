## ASDL xDSL/IR Refactor – Design Log (Living Document)

This document is the authoritative, evolving record for refactoring `asdlc` around a formal IR, starting with xDSL and optionally inter-operating with MLIR later. It captures decisions, rationale, milestones, risks, and references. Keep updates concise, high-signal, and dated.

### Project Overview & Goals
- **Goal**: Introduce a formal IR and pass infrastructure to improve modularity, diagnosability, and extensibility of parsing → elaboration → validation → generation.
- **Approach**: Keep the existing AST (dataclasses) for syntax; add an xDSL-based IR with passes for elaboration and validation; migrate generation to lower from IR.
- **Constraints**: Maintain CLI compatibility and legacy pipeline via a toggle until IR pipeline reaches parity.

### Current Architecture Snapshot
- Parser, elaborator (pattern/variables/env), validator, generator, and import system are functional with comprehensive unit tests. See `context/memory.md` for latest status.
- Visualizer pipeline and CLI exist; not directly impacted by initial IR bring-up.

### Framework Decision (xDSL first, MLIR optional)
- **Decision**: Adopt xDSL (Python-native) for Phase 0–3; evaluate MLIR interop after IR semantics stabilize.
- **Rationale**: Rapid iteration in Python, simpler integration with current codebase and tests, shared textual format with MLIR enables later interop.
- **Status**: Accepted (2025-10-09). Dependency pin TBD after CI validation on Python 3.10+.

### Dialect Design (initial)
- **ModuleOp**: attributes `{ name: StringAttr, parameters: DictAttr, variables: DictAttr, ports: ArrayAttr<PortAttr>, spice_template?: StringAttr }`; single region with one block.
- **Port representation**: block arguments annotated with `PortAttr{ name, direction: (in|out|inout), kind: (analog|digital) }`. Extendable with `supply`, `bulk` later.
- **WireOp** (first-class nets): `{ name: StringAttr, width?: IntegerAttr|RangeAttr }`. Prefer explicit scalar wires after pattern expansion; bus width may be retained temporarily pre-expansion.
- **InstanceOp**: `{ sym_name, model_ref, parameters: DictAttr, pin_list: ArrayAttr<StringAttr> }` with operands referencing `WireOp`s. Instance does not yield results; connectivity is through uses of `WireOp`.
- **Locations**: All ops carry source locations from AST for diagnostics.

### IR Semantics and Wiring Model
- Nets are modeled as dedicated `WireOp`s; instances consume wires via operands, avoiding multi-result SSA modeling for devices with many-to-many pin wiring.
- Port nets are block arguments of `ModuleOp`'s entry block; internal nets are `WireOp`s inside the module block.
- Pattern/bus expansions materialize concrete wires and instances prior to validation/generation.

### Passes (order and scope)
1) **PatternExpansionPass**: Expand literal `<...>` and bus `[msb:lsb]` patterns across ports, nets, instance ids; create concrete `WireOp`s and `InstanceOp`s.
2) **VariableResolutionPass**: Replace instance parameter values that reference module variables; error on unknowns.
3) **EnvVarPass**: Resolve `${VAR}` in parameters and `spice_template`; emit diagnostics if missing/invalid.
4) **Validator (analysis) passes**:
   - Port mapping check (instance pins vs target module ports)
   - Parameter override rules (hierarchical vs primitive)
   - Module parameters rule (no params on hierarchical)
   - Later: undeclared nets, unused modules (currently suppressed in legacy)

### Import Strategy
- Phase 0–2: Retain the current import system and flatten modules before AST→IR conversion for minimal churn.
- Optional later: IR-level import pass for merging modules if benefits emerge.

### CLI & Dev UX
- Add `asdlc ir-dump` to run parse → import(flatten) → AST→IR and print IR; support `--run-pass` to run selected passes.
- Introduce `--engine {legacy,xdsl}` (default: `legacy`) for elaborate/netlist commands; IR path remains opt-in until parity.

### Testing & Parity Strategy
- Unit tests under `tests/unit_tests/ir/`:
  - Dialect printing/parsing and AST→IR conversion for small primitive and hierarchical modules
  - PatternExpansionPass cases for `<p,n>` and `[msb:lsb]`
- Golden textual IR files for readability and stability.
- E2E parity tests: compare legacy vs IR-generated SPICE on selected examples:
  - `examples/libs/ota_single_ended/miller_ota/miller_ota.asdl`
  - `examples/libs/ota_single_ended/ota_5t/`
  - One representative Gray–Meyer figure

### Migration Phases (high-level)
- **Phase 0**: Scaffold ASDL dialect, register ops/attrs, `asdlc ir-dump`, optional dependency and CI job.
- **Phase 1**: Implement AST→IR with locations; PatternExpansionPass; `ir-dump --run-pass pattern-expansion`.
- **Phase 2**: VariableResolutionPass and EnvVarPass with diagnostics parity.
- **Phase 3**: Port validator rules as IR analyses; maintain legacy validator for comparison.
- **Phase 4**: SPICE generator lowering from IR; achieve parity on sample designs.
- **Phase 5**: Toggle default engine after parity; deprecate legacy elaborator/validator steps when safe.

### Risks & Mitigations
- **SSA vs wiring semantics**: Using `WireOp` avoids awkward multi-result device modeling; validates many-to-many connections cleanly.
- **Performance**: Python overhead acceptable initially; keep passes simple; measure on large designs; consider MLIR lowering later if needed.
- **Bus semantics**: Make expansion deterministic early; prefer explicit scalar wires post-expansion.
- **Interop complexity**: Defer MLIR interop until IR stabilizes; rely on shared textual format for future bridging.

### Open Questions
- Do we need early port kinds beyond `analog` (e.g., `supply`, `bulk`) for validator/generator rules?
- Finalize the E2E parity example set—OK to proceed with `miller_ota` and `ota_5t` first?
- xDSL pin: propose after initial CI validation on macOS Python 3.10 (venv).

### Decision Log
- 2025-10-09 — Adopt xDSL first; keep MLIR interop optional
  - Rationale: iteration speed, alignment with Python stack, later MLIR possible
  - Impact: optional dependency, new CLI, IR-based passes introduced incrementally

### E2E Plan Review – 2025-10-09
- Strengths
  - Minimal dialect (`ModuleOp`, `InstanceOp`, `WireOp`, `PortAttr`) and `ExprAttr` future-proofing
  - Deterministic naming in PatternExpansion; direct SPICE emitter to accelerate parity
  - Goldens + normalized diffing for IR/SPICE to stabilize CI
- Required add-ons
  - Symbols/uniqueness: enforce unique `ModuleOp` symbols, `WireOp.name` per module, and `InstanceOp.sym_name`
  - Canonical pin ordering: verify `len(operands) == len(pins)`; names match callee ports; emitter respects `pins` order
  - Diagnostics mapping: align verifier/analysis diagnostics with XCCSS codes (E/V scheme)
  - Number/string normalization: standardized param order and float formatting; add parity normalizer for SPICE diffs
  - Location fidelity: use `FusedLoc` for expansions (original + expansion site)
  - Performance: cache symbol lookups and name canonicalization in passes
  - CLI UX: `--run-pass ... --verify` returns non‑zero on failure; support `--print-after`
  - CI: pin `xdsl` in optional extra; test macOS/Ubuntu on Py 3.10/3.11 with cached wheels
- Minor spec tweaks
  - Duplicate checks for symbols/wires/instances; `WireOp` must have no width post-expansion
  - Deterministic name helper with collision diagnostics and fix‑it suggestions
  - Negative test: unresolved `ExprAttr` cannot reach emitter


### Immediate Action Items (Phase 0)
- Scaffold dialect and register ops/attrs
- Implement AST→IR conversion skeleton (flattened `ASDLFile` input)
- Add `asdlc ir-dump` with textual printing and `--run-pass`
- Add CI job to import xDSL and run a smoke test on tiny example

### Kickoff Checklist – Phase 0 (Execution)
- Continue on current branch `xdsl_refactor` (no new branch)
- Dependency: add optional extra for `xdsl` and pin after CI green
- Dialect: define and register `ModuleOp`, `InstanceOp`, `WireOp`, `PortAttr`, `RangeAttr`, `ExprAttr`
- Verifier skeletons: module/instance/wire uniqueness; pin count/name checks
- Converter: AST (flattened) → IR skeleton with locations
- CLI: implement `asdlc ir-dump --verify --run-pass <list>`
- Tests: create dedicated fixture ASDL files under `tests/fixtures/ir/`; avoid referencing `examples/`
- Helpers: deterministic name canonicalizer; SPICE parity normalizer stub
- Diagnostics: map new verifier/analysis messages to XCCSS code scheme
- CI: macOS + Ubuntu on Py 3.10/3.11 with `xdsl` extra; run smoke + goldens
- Deliverable: IR prints and verifies on fixture designs (parity is approximate initially)

### References (repo-local)
- High-level plan and rationale: `doc/dsl_framework/xdsl_refactor_plan.md`
- Pattern expansion legacy logic: `src/asdl/elaborator/pattern_expander.py`
- Visualizer CLI context: `context/memory.md` (Visualizer sections)
- CLI architecture and commands: `doc/cli/`
- Testing organization: `tests/unit_tests/`

### Appendix: Context Excerpts
Key excerpted intent from `doc/dsl_framework/xdsl_refactor_plan.md`:

```72:76:doc/dsl_framework/xdsl_refactor_plan.md
Adopting xDSL – Overview
xDSL is a Python framework for constructing MLIR‑like intermediate representations. It provides classes such as IRModule, Block, Operation, Attribute and Type and allows users to define custom dialects with operations and attributes. xDSL also comes with a pass infrastructure for running transformations and analyses. Adopting xDSL would modernize the ASDL compiler by introducing:
A formal IR: Modules, instances and nets would become operations in a custom ASDL dialect. Each operation can carry attributes (e.g., parameter dictionaries) and results (e.g., nets). An IRModule would hold all module definitions as regions.
Passes: Pattern expansion, variable resolution, import flattening and validation rules can be implemented as passes over the IR. xDSL’s pass manager can orchestrate these passes.
```

### Design Decisions – 2025-10-09 (Approved/Scoped)
- xDSL‑first with MLIR interop later — APPROVED
  - Rationale: Faster iteration in Python; shared textual format enables future MLIR interop.
- AST as the sole editable source; IR is derived only — APPROVED
  - Rationale: Preserve round‑trip fidelity and comments; keep IR for analysis/passes/generation only.
- ruamel round‑trip YAML for persistence to preserve comments — APPROVED
  - Rationale: Safe agent edits and minimal diff noise; retain formatting and comments.
- Parity targets — SCOPED
  - Initial focus: `examples/libs/ota_single_ended/miller_ota/miller_ota.asdl` only.
  - Note: Current one‑liner device instantiations may hinder round‑trip‑safe operations. Consider enabling a multi‑line instance formatting option in the pretty‑printer to offer stable anchors for AI edits. Track as part of AST API style options.

### Pending Decision – AST API Namespace
- Proposal: Create `src/asdl/ast_api/` with a transactional `ChangeSet` model
  - Query/edit surface: typed getters, structured queries, and mutation ops returning a `ChangeSet`
  - Safety: pre‑commit validation, diff preview, rollback
  - Status: PENDING APPROVAL

```110:119:doc/dsl_framework/xdsl_refactor_plan.md
5. Generate output from IR
Once elaboration and validation passes complete, the IR can be lowered to a target format. For example:
Spice netlist generator: Traverse the IRModule and emit subcircuit definitions (.subckt), port lists, instance lines and .ends. The xDSL IR ensures that ports and nets are properly expanded and mapped.
Visualization or debug output: Use xDSL’s printing facilities to display the IR for debugging or to feed into other analysis tools.
6. Migration strategy
Phase 1 – non‑disruptive integration: Add the xDSL dialect and IR conversion alongside the existing compiler. Implement passes but keep the existing elaborator/validator in place. Provide a command‑line option to output the xDSL IR after parsing for experimentation.
Phase 2 – replace elaboration: Gradually migrate pattern expansion, variable resolution and environment resolution to xDSL passes. Use the existing Elaborator as a wrapper that invokes the pass manager.
```


