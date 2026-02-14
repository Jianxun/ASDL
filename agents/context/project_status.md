# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- ASDL docs pipeline is focused on Sphinx (Tier 2); Markdown generation is deprecated.
- Comment-based docstring extraction is implemented per ADR-0021 and feeds Sphinx rendering.
- Doc rendering targets per-file `asdl:document` pages plus project-level manifest wiring.
- Dependency graph support is the active enabler for instance cross-links and "Used by" sections.
- Agreed doc structure: page title is the ASDL file name with extension; file-level Overview and Imports live at the document level; module sections render Notes (module-level overview), Interface (name + description), Instances, Nets, and Used by.
- ASDL authoring ergonomics work is now scoped to a fresh extension package at `extensions/asdl-language-tools/` with a dedicated spec and ADR.

## Last verified status
- `venv/bin/pytest tests/unit_tests/ast`
- `venv/bin/pytest tests/unit_tests/ir`
- `venv/bin/pytest tests/unit_tests/parser`
- `venv/bin/pytest tests/unit_tests/emit -v`
- `venv/bin/pytest tests/unit_tests/netlist`
- `venv/bin/pytest tests/unit_tests/e2e`
- `venv/bin/pytest tests/unit_tests/cli`
- `venv/bin/pytest tests/unit_tests/ir tests/unit_tests/netlist`
- `venv/bin/python -m py_compile src/asdl/emit/netlist/*.py`

## Next steps (1-3)
1. T-275: scaffold `extensions/asdl-language-tools/` and ship net-first syntax highlighting/snippets baseline.
2. T-276: implement Python completion worker reusing ASDL parser/import/config internals.
3. T-277: wire extension completion provider to worker with robust fallback behavior.

## Risks / unknowns
- Module name collisions across files must be disambiguated in tooling without exposing hash IDs to users.
- Sphinx link resolution depends on depgraph completeness; unresolved refs should degrade gracefully.
- Sphinx docs builds currently miss `.asdlrc` lib roots unless explicitly wired, leading to AST-010 import errors.
- Manifest auto-expansion must avoid non-deterministic ordering and duplicates across entry imports.
- Current Sphinx output still shows nested/duplicate headings for some files; likely remaining mismatch in document/module section ordering.
- Python worker runtime/discovery across local dev environments may introduce startup friction for extension users.
