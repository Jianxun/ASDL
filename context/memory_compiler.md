# Compiler Memory – Parser and IR Scaffold Notes

## Parser Module (src/asdl/parser)
- Entrypoint: `ASDLParser.parse_file(filepath) -> (ASDLFile|None, List[Diagnostic])`
- Modular components:
  - `core`: `YAMLLoader`, `LocatableBuilder`
  - `sections`: `FileInfoParser`, `ImportParser`, `ModelAliasParser`, `PortParser`, `InstanceParser`, `ModuleParser`
  - `resolvers`: `DualSyntaxResolver` (maps legacy/modern keys), `FieldValidator`
- Outputs `src/asdl/data_structures` dataclasses with locations via `Locatable`.
- AST root: `ASDLFile{ file_info, modules, imports?, model_alias? }`.
- Ordering: port declarations are in a dict that preserves insertion order (CPython ≥3.7). Treat order as significant; do not sort in printers.

## Data Structures (src/asdl/data_structures)
- `Port` fields: `dir: PortDirection`, `type: PortType`.
- `Module` fields:
  - `ports: Dict[str, Port]` (ordered), `instances: Dict[str, Instance]` (ordered)
  - `internal_nets: List[str]`, `parameters`, `variables`, `spice_template?`
  - Invariants: either `spice_template` or `instances` (mutually exclusive);
    at least one must be present (enforced in `__post_init__`).
- `Instance` fields: `model: str`, `mappings: Dict[str,str]`, `parameters?`.

## CLI (src/asdl/cli)
- Group: `asdl.cli:cli` registered in `pyproject.toml [project.scripts]`.
- New command: `ir-dump` (Phase 0)
  - Flags: `--verify`, `--run-pass` (no-op for now), `--json`, `-v`.
  - Flow: parse → minimal verify → textual IR print.

## IR Scaffold (src/asdl/ir)
- `build_textual_ir(asdl_file: ASDLFile) -> str` prints:
  - Header: `asdl.module_set top=... doc='...'`
  - For each module (in dict order):
    - `module @<name> params={...}`
    - Ports in declared order: `%port <name> dir=<in|out|in_out> kind=<signal|power|...>`
    - Instances in dict order: `%inst <id>: model=<model> mappings={...} params={...}`
    - `endmodule`
- Port order invariant preserved by iterating the dict as-is; no sorting.

## xDSL Engine (Phase 0 status)
- Dialect stubs added under `src/asdl/ir/xdsl_dialect/`:
  - Ops: `asdl.module`, `asdl.instance`, `asdl.wire` (minimal attributes)
  - Attrs: `asdl.port`, `asdl.range`, `asdl.expr` (placeholders)
- CLI: `asdlc ir-dump --engine {textual,xdsl}`; textual default remains.
- Converter: `src/asdl/ir/converter.py` builds `builtin.module` containing `asdl.module` with:
  - attributes: `sym_name`, empty `parameters`/`variables`, `ports` as `ArrayAttr<StringAttr>` preserving order
  - a single empty body region (entry block)
- Printing (current xDSL version):
  - Example output: `builtin.module { "asdl.module"() ({ ^bb0: }) {sym_name = "prim", parameters = {}, variables = {}, ports = ["a", "b", "c"]} : () -> () }`
- Pass hook: `src/asdl/ir/passes.py` provides a no-op `run_passes` placeholder.
- Tests: fixture-based IR tests added under `tests/unit_tests/ir/` (port order, CLI smoke for textual and xDSL engines).

## Netlist IR (Phase 0 – minimal lowering and emitter)
- Dialect: `netlist` added under `src/asdl/ir/netlist_dialect/` with:
  - Ops: `netlist.module{ sym_name, ports: ArrayAttr<StringAttr>, parameters: DictAttr }`
  - Ops: `netlist.instance{ sym_name, model_ref, pin_map: DictAttr(port->net), pin_order: ArrayAttr<StringAttr>, parameters: DictAttr }`
- Lowering: `asdl_ast_to_netlist_module(asdl_file)` builds a `builtin.module` of `netlist.module` ops and nested `netlist.instance` ops.
  - `pin_map` preserves named connectivity; `pin_order` aligns to callee port order to support positional emitters.
  - Parameters are not propagated yet (next step); imports/model aliases unresolved by design in Phase 0.
- Textual netlist emitter: `emit_netlist_text(builtin_module, dialect=...)` in `src/asdl/ir/netlist_text.py`.
  - Dialects: `ngspice` (positional pins; `.subckt` / `.ends`) and `neutral` (named pins `pin=net`).
  - CLI: `asdlc ir-dump --engine xdsl --lower netlist-text --sim {ngspice|neutral} file.asdl`.
  - Example (ngspice): `Xmn_in_p vd vin_p tail vss nmos`.

## Decisions Captured
- Preserve declared port order across AST → IR → SPICE.
- Defer PatternExpansionPass to next phase; Phase 0 focuses on AST plumbing and IR dump.

## Follow-ups (Next Session)
- Add unit test under `tests/unit_tests/ir/` to assert port order preservation.
- Optionally include `internal_nets` and `variables` in textual IR (retain order).
- Plan xDSL dialect skeleton (`ModuleOp`, `InstanceOp`, `WireOp`, `PortAttr`...) with ordered port list attribute.


