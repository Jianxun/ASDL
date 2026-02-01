# Spec — ASDL Docstrings (Comment-Based) v0.1

## Purpose
Define how design intent embedded as YAML comments in ASDL files is extracted
and rendered into documentation, with a focus on ports/pins as the contract
surface between blocks. Markdown generation and Sphinx rendering are both
supported outputs.

## Scope
- Applies to documentation generation only; comments are not part of the AST.
- Uses comment-preserving parsing (ruamel.yaml) against raw ASDL YAML.
- Targets Markdown output and Sphinx rendering via Tier 1/2 tooling.

## Conventions
- A **comment block** is one or more consecutive `#` lines with no blank lines
  between them.
- A **key** is a mapping key at any indentation level (e.g., `nets`, `L`, `$VDD`).
- A **key/value pair** is a line that defines a mapping entry (scalar, list, or
  nested mapping).
- Blank lines terminate a comment block's association.

## Docstring extraction rules

### 1) File docstring
If the file begins with a comment block before any non-comment content, that
block becomes the **document-level docstring**.

### 2) Key docstring (block comments)
A comment block immediately above a key at the same indentation level attaches
to that key. There must be no blank line between the block and the key.

### 3) Inline comments
An inline comment on the same line as a key/value pair attaches to that key.
If the key already has a block docstring, the inline comment is appended as a
second paragraph.

Example inline association:
```yaml
mp: gf.pfet_03v3 L={L} W={W} NF={NF} m=3 # PMOS/NMOS ratio is 3:1
```

### 4) Section/bundle docstrings
Inside a mapping, a comment block followed by **two or more** contiguous
key/value pairs at the same indentation is a **section docstring** for that
bundle of keys. The bundle ends at the first of:
- a blank line
- another comment block at the same indentation
- a dedent

If only one key/value pair follows the block, treat it as a key docstring
instead of a section docstring.

## Comment text normalization
- Strip the leading `#` and a single following space if present.
- Preserve internal line breaks within a block.
- Trim leading/trailing blank lines after normalization.

## Examples

### Per-key and inline docstrings (swmatrix_Tgate)
```yaml
modules:
  # Switch Matrix Tgate
  swmatrix_Tgate:
    variables:
      L: 0.28u
      W: 8u
      NF: 6
    instances:
      mn: gf.nfet_03v3 L={L} W={W} NF={NF} m=1
      mp: gf.pfet_03v3 L={L} W={W} NF={NF} m=3 # PMOS/NMOS ratio is 3:1
    nets:
      $VDDd: [<inv1|inv2|nand2>.<VPWR|VNB>, mp.b] # nominal 3.3V
      $T1: [<mn|mp>.d] # Tgate analog terminal 1
```

### Section/bundle docstrings (full_switch_matrix_130_by_25)
```yaml
nets:
  # data chain
  $data: [sw_row<1>.D_in]
  $D_out: [sw_row<130:130>.D_out]
  D<129:1>: [sw_row<130:2>.D_in, sw_row<129:1>.D_out]

  # clock broadcast
  $PHI_1_in: [sw_row<@ROW>.PHI_1]
  $PHI_2_in: [sw_row<@ROW>.PHI_2]
  $enable_in: [sw_row<@ROW>.enable]
```

## Documentation layout (recommended)

### Document
- Title (file name or top module name)
- Overview (file docstring or top module docstring)
- Imports (table: alias, path, docstring)
- Modules (one section per module)

### Module section
- Interface (Ports/Pins) **contract**
  - Table: `name`, `kind` (power/ground/digital/analog/clock/inout), `direction`
    (if known), `description`
  - Source: `$`-prefixed net keys in `nets` + any docstrings that indicate
    external pins.
- Parameters / Variables
  - Table: `name`, `default`, `description`
- Instances
  - Table: `instance`, `ref`, `params`, `description`
  - When possible, `ref` should link to the referenced module definition.
  - Display rule: show the module `name` only; if collisions are present in the
    current page scope, disambiguate with `name (relative/path.asdl)` rather
    than any hash-based ID.
- Used by (optional)
  - List modules that instantiate this module when a dependency graph is available.
  - Display rule: same as instances; never expose hash-based IDs unless in a
    debug context.
- Nets
  - Group by section/bundle docstrings when present.
  - For each net: `name`, `endpoints`, `description`
- Patterns / Arrays (if present)
  - List pattern definitions and their docstrings.
- Notes / Specs
  - Freeform specs or constraints captured in module-level comments.

## Build modes

### Tier 1 (Markdown)
- `scripts/gen_asdl_docs.py` renders per-file Markdown docs.
- Sphinx can ingest the Markdown with MyST, but cross-refs are limited to
  emitted domain directives.

### Tier 2 (Sphinx-native)
- `asdl:document` renders a single ASDL file directly into a Sphinx page.
- `asdl:library` renders all `.asdl` files under a directory.
- Project manifests may list entry files to generate per-file pages.
- Instance links and "Used by" sections are driven by a dependency graph.

## Dependency graph (Tier 2)
- The `asdlc depgraph-dump` command emits a resolved graph that maps module
  definitions to instance refs across files.
- The Sphinx extension may load this graph to enable instance cross-links and
  "Used by" sections.
### Module identity and collisions
- Module names must be unique within a file; same-name modules across files are
  allowed.
- Use a deterministic internal module identifier:
  `module_id = "{name}__{hash8}"`, where `hash8 = sha1(file_id)[:8]`.
- `module_id` is for tooling (JSON keys, anchors, cross-links). User-facing
  docs should display `name` only; when disambiguation is needed, show
  `name (relative/path.asdl)` rather than the hash.

## Non-goals
- No AST schema changes and no requirement to add `doc` or `metadata` fields.
- No comment extraction from list items or scalar values outside mapping keys.
