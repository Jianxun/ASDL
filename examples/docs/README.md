# ASDL Library Docs

This directory holds generated Markdown documentation for ASDL libraries under
`examples/libs/`. The renderer pulls comment-based docstrings from ASDL YAML
files and formats them into module-level reference docs.

## Generate docs

```bash
venv/bin/python scripts/gen_asdl_docs.py \
  examples/libs/sw_matrix \
  --out examples/docs/libs
```

The generator scans directories recursively and writes one Markdown file per
ASDL source, using the input file stem as the output filename.
If multiple sources share the same stem, the generator reports a collision.

To include archived examples under `_archive`, add `--include-archive`.

## Build docs

Install the docs requirements (see `examples/docs/requirements.txt`), then build HTML:

```bash
./venv/bin/sphinx-build -b html examples/docs examples/docs/_build/html
```
