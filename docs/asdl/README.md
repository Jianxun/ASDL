# ASDL Markdown Docs

This directory holds generated Markdown documentation for ASDL sources. The
renderer pulls comment-based docstrings from ASDL YAML files and formats them
into module-level reference docs.

## Generate docs

```bash
venv/bin/python scripts/gen_asdl_docs.py \
  examples/libs/sw_matrix/swmatrix_Tgate/swmatrix_Tgate.asdl \
  --out docs/asdl
```

The generator writes one Markdown file per input source, using the input file
stem as the output filename.

## Build docs

Install the docs requirements (see `docs/requirements.txt`), then build HTML:

```bash
./venv/bin/sphinx-build -b html docs docs/_build/html
```
