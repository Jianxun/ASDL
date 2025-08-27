# ASDL Examples

This directory contains ASDL (Analog Structured-Description Language) examples that match the current schema (generated via `asdlc schema`).

Regenerate schema documentation: `bash doc/schema/generate.sh`.

## Up-to-date Examples

- Toy import composition (under `examples/imports/toy/`):
  - `primitives.asdl`: Primitive device library with `spice_template` modules
  - `opamp.asdl`: Uses `imports` and `model_alias` to reference primitives
  - `top.asdl`: Top-level design instantiating `opamp.ota_diffpair`

These demonstrate:
- Unified `Module` (primitive vs hierarchical)
- Port directions and types (`power`, `ground`, etc.)
- Instances with port-to-net `mappings`
- Import and alias resolution

## Notes

- Older `.yml` examples are legacy and may not reflect the current schema semantics (e.g., removed constraints). Prefer the `.asdl` files above.