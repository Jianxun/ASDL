## SPICE Netlist Generation

### Purpose and Scope
This document describes the design decisions, options, and algorithms used by the SPICE netlist generator in ASDL. It covers inputs/outputs, deterministic ordering, subcircuit construction, instance rendering, diagnostics, and CLI integration.

### Inputs and Outputs
- **Input**: An elaborated and validated `ASDLFile` (`src/asdl/data_structures/structures.py`) containing unified `Module` definitions (primitive or hierarchical).
- **Output**: A single SPICE netlist string written by the CLI to a `.spice` file.

### Key Design Decisions
- **Unified generation**: One generator handles both primitive and hierarchical modules via a single `Module` type.
- **No XMAIN**: The generator does not emit a top-level instantiation line. Top-level content is expressed as a `.subckt` body; higher-level orchestration may choose how to include/simulate it.
- **No automatic PDK includes**: PDK `.include` lines are not injected by the generator. Header/footer injection is the responsibility of an orchestrator or caller.
- **Deterministic output**: Emission order and formatting are deterministic across runs.

### Options and CLI
- `TopStyle` (`src/asdl/generator/options.py`):
  - `subckt` (default): emit normal `.subckt {top} … .ends` for the top module.
  - `flat`: comment only the top wrappers while preserving the body, to enable “flat” top-level content when embedded elsewhere.
- CLI flags (`src/asdl/cli/netlist.py`):
  - `--top-style {subckt,flat}` threads an instance of `GeneratorOptions` into `SPICEGenerator`.
  - `-t, --template` enables template mode: unresolved placeholder checks are skipped and default output suffix is `.spice.j2`.

### Emission Order (Dependency Ordering)
Implemented in `src/asdl/generator/ordering.py`.
- **Graph**: Nodes are hierarchical modules (those with `instances`). Edges are parent → child for hierarchical children only (primitive references do not create nodes/edges).
- **Algorithm**: Depth-first search with postorder appends for children-first emission; cycle back-edges are ignored to terminate safely (validator should catch cycles earlier).
- **Top handling**:
  - If `file_info.top_module` is a hierarchical module, traverse its subgraph first. Emit all children before the top; the top is emitted last.
  - Then emit hierarchical modules not reachable from top ("orphans") in deterministic order.
- **Determinism**: Iteration respects insertion order of `asdl_file.modules` and instance maps.

### Subcircuit Construction
Implemented in `src/asdl/generator/subckt.py`.
- Header line: `.subckt {module_name} {port_1} {port_2} …` with ports in declaration order (`formatting.get_port_list`).
- Instance lines: one per child instance, indented by two spaces.
- End line: `.ends`.
- `TopStyle.FLAT`: when building the top module only, the header and end lines are prefixed with `*` while the body remains unchanged.

### Instance Rendering
Implemented in `src/asdl/generator/instances.py` with helpers:
- **Primitive instances** (`templates.generate_primitive_instance`):
  - Template data is constructed from `name`, `mappings`, `parameters` (module defaults merged with instance overrides), and `variables`.
  - Variable values override parameters with a `G0601` warning.
  - Unknown template keys are left as `{placeholder}` tokens for postprocessing to detect.
- **Hierarchical calls** (`calls.generate_subckt_call`):
  - Node order follows the callee’s port declaration order.
  - Parameters are formatted as sorted `name=value` pairs.

### Defensive Guards and Diagnostics (XCCSS)
Diagnostics are defined in `src/asdl/generator/diagnostics.py` and created via `create_generator_diagnostic`.
- `G0102` Top Module Not Found (ERROR): top specified but absent from `modules`.
- `G0201` Unconnected Port in Subcircuit Call (ERROR): instance missing mappings for callee ports.
- `G0301` Cannot Generate SPICE (ERROR): module has neither `spice_template` nor `instances`.
- `G0305` Unresolved Template Placeholder (**WARNING**): single-brace `{placeholder}` remains after rendering.
  - In template mode (`--template`), this check is skipped entirely.
- `G0602` Jinja Template Placeholder Detected (**WARNING**): double-brace `{{ placeholder }}` detected in output. Suggest using `--template` to emit `.spice.j2` and suppress placeholder warnings.
- `G0401` Unknown Model Reference (ERROR): instance references a missing module.
- `G0601` Variable Shadows Parameter (WARNING): variable overwrites parameter during primitive rendering.
- `G0701` Missing Top Module (WARNING): no top specified; generation proceeds as a library.

### Postprocessing
Implemented in `src/asdl/generator/postprocess.py`.
- Scans the final output for placeholders and emits diagnostics:
  - Single braces `{...}` → `G0305`.
  - Double braces `{{...}}` → `G0602` with suggestion to use `--template`.
  - In template mode, placeholder scanning is skipped.

### Formatting Rules
- Comment character: `*`.
- Indentation: two spaces for nested content.
- Port order: preserved from module declaration order.
- Parameter order: sorted by name when rendering instance named parameters.

### End-to-End Flow
`src/asdl/generator/spice_generator.py` orchestrates generation:
1) Header metadata comments (doc, top, author, date, revision)
2) Invalid module comments and `G0301` diagnostics
3) Hierarchical subcircuits in dependency order (top last)
4) Top presence diagnostics (`G0102` or `G0701`)
5) Trailing `.end`
6) Postprocess for placeholders (`G0305` for `{}`, `G0602` for `{{}}`; skipped in template mode)

### Example
Given modules `child`, `parent`, and `top` where `top` instantiates `parent`, and `parent` instantiates `child`:

```spice
* SPICE netlist generated from ASDL
* Design: Example
* Top module: top

* Hierarchical module subcircuit definitions
.subckt child a
.ends

.subckt parent p
  X_U1 n1 child
.ends

.subckt top t
  X_U2 n2 parent
.ends

.end
```

With `--top-style flat`, only the top wrappers are commented:

```spice
* Hierarchical module subcircuit definitions
.subckt child a
.ends

* .subckt top t
  X_U2 n2 parent
* .ends

.end
```

### Limitations and Future Work
- Cycle handling is best-effort in the generator; proper cycle detection and reporting should occur in validation.
- Header/footer injection (e.g., simulator directives, includes) is out of scope for the generator; consider orchestrator-level templates.
- Additional styles (e.g., inlining top body without wrappers) could be introduced if justified by downstream flows.


