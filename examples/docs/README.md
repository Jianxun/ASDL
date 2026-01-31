# ASDL Library Docs

This directory holds Sphinx documentation for ASDL libraries under
`examples/libs/`. The docs build directly from the source `.asdl` files via the
``asdl:library`` directive, which renders the docstrings into module-level
reference docs without pre-generated Markdown.

## Optional: generate Markdown

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
