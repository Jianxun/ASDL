# ASDL Library Docs

This directory holds Sphinx documentation for ASDL libraries under
`examples/libs/`. The docs build directly from the source `.asdl` files via the
``asdl:library`` directive, which renders the docstrings into module-level
reference docs without pre-generated Markdown.

## Source mapping

The docs use the Tier 2 Sphinx directives directly:

- `.. asdl:library:: ../libs` renders all library `.asdl` files.
- `.. asdl:document:: path/to/file.asdl` renders a single file.

## Build docs

Install the docs requirements (see `examples/docs/requirements.txt`), then build HTML:

```bash
./venv/bin/sphinx-build -b html examples/docs examples/docs/_build/html
```
