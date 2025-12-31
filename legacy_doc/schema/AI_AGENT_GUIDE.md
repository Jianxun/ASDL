## ASDL for AI Agents — Quick Guide

This guide complements the auto-generated schema (`schema.json`, `schema.txt`) and explains how another AI agent should read and produce ASDL documents.

### What is ASDL?
ASDL (Analog Structured-Description Language) is a YAML-based format to describe analog designs as a set of modules with ports, parameters/variables, and hierarchical instances. The canonical model lives in code under `src/asdl/data_structures/structures.py` and the CLI can emit the schema users see.

### Where is the truth?
- **Single source of truth**: `src/asdl/data_structures/structures.py`
- **Auto-generated docs**: `doc/schema/schema.json` (machine), `doc/schema/schema.txt` (human)
- **Regenerate docs**: `bash doc/schema/generate.sh`

### Core objects at a glance
- **ASDLFile**: The YAML document root
  - `file_info` (required): metadata (top module name, author, etc.)
  - `modules` (required): `{ <module_name>: Module }`
  - `imports` (optional): `{ <alias>: path/to/file.asdl }`
  - `model_alias` (optional): `{ <local_name>: "<import_alias>.<module>" }`
  - `metadata` (optional): open extension bag

- **Module** (unified; primitive OR hierarchical)
  - Common: `doc?`, `ports?`, `internal_nets?`, `parameters?`, `variables?`, `pdk?`, `metadata?`
  - Primitive: `spice_template` (string). The placeholder `{name}` is implicitly available and resolves to the instance id.
  - Hierarchical: `instances` → `{ <instance_id>: Instance }`
  - Constraint: must have exactly one of `spice_template` or `instances`.
  - Nets: Each declared port implicitly defines an interface net with the same name. Use `internal_nets` for additional local nets.

- **Port**
  - `dir` (required): one of `in`, `out`, `in_out`
  - `type` (optional): one of `signal`, `power`, `ground`, `bias`, `control` (default: `signal`)
  - `metadata?`

- **Instance**
  - `model` (required): name of a `Module`
  - `mappings` (required): `{ <port_name>: <net_name> }` — Keys must match the referenced module’s declared ports.
  - `doc?`, `parameters?`, `metadata?`

### Enums
- `PortDirection`: `in | out | in_out`
- `PortType`: `signal | power | ground | bias | control`

### Requireds and defaults
- A field is required if the dataclass has no default.
- Example default: `Port.type` defaults to `signal`.
- Defaults appear in `schema.json` as `default` and in `schema.txt` comments.

### Imports and aliases (authoring intent)
- `imports` declares file aliases for external `.asdl` files: `{ alias: path }`.
- `model_alias` provides local short names for imported modules: `{ local: "alias.module" }`.
- Downstream import elaboration resolves and flattens these into a single `ASDLFile` before generation.

### Minimal YAML example
```yaml
file_info:
  top_module: inverter

modules:
  inverter:
    ports:
      in: { dir: in, type: signal }
      out: { dir: out, type: signal }
      vdd: { dir: in, type: power }
      vss: { dir: in, type: ground }
    instances:
      m1: { model: nmos, mappings: { d: out, g: in, s: vss, b: vss } }
      m2: { model: pmos, mappings: { d: out, g: in, s: vdd, b: vdd } }
  nmos:
    spice_template: "{name} {d} {g} {s} {b} nmos l={L} w={W}"
  pmos:
    spice_template: "{name} {d} {g} {s} {b} pmos l={L} w={W}"
```

### Authoring tips for AI agents
- Ensure each `Module` is either primitive (`spice_template`) or hierarchical (`instances`), not both.
- For hierarchical instances, map all required ports to nets. The validator will flag missing connections.
- Prefer setting `file_info.top_module` and ensure it references a module present in `modules`.
- Use `parameters` and `variables` for numeric/string values only; expressions/patterns are resolved in elaboration phases.
- Parameters vs variables: Parameters define overridable knobs (instances may override via `Instance.parameters`); variables are computed/derived and not overridable by instances.
- Use `metadata` for extensible hints (layout, optimization, tool-specific options). Unknown keys should be preserved by tools.
 - PDK: The `pdk` field is informational; automatic `.include` emission is deprecated and handled outside the generator.

### CLI that users see
- Print human schema: `asdlc schema`
- Print JSON schema: `asdlc schema --json`
- Write both into `doc/schema/`: `bash doc/schema/generate.sh`

### How to stay in sync
- The schema docs are generated from code; avoid hardcoding structures in docs.
- Update the dataclasses in `structures.py`; then re-run the generator script.

### Useful references in this repo
- Data structures: `src/asdl/data_structures/structures.py`
- Schema generator: `src/asdl/data_structures/schema_gen.py`
- CLI command: `src/asdl/cli/schema.py`
- Generated docs: `doc/schema/schema.json`, `doc/schema/schema.txt`


