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

## Decisions Captured
- Preserve declared port order across AST → IR → SPICE.
- Defer PatternExpansionPass to next phase; Phase 0 focuses on AST plumbing and IR dump.

## Follow-ups (Next Session)
- Add unit test under `tests/unit_tests/ir/` to assert port order preservation.
- Optionally include `internal_nets` and `variables` in textual IR (retain order).
- Plan xDSL dialect skeleton (`ModuleOp`, `InstanceOp`, `WireOp`, `PortAttr`...) with ordered port list attribute.


