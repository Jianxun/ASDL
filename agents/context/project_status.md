# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- ASDL docs pipeline is focused on Sphinx (Tier 2); Markdown generation is deprecated.
- Comment-based docstring extraction is implemented per ADR-0021 and feeds Sphinx rendering.
- Doc rendering targets per-file `asdl:document` pages plus project-level manifest wiring.
- Dependency graph support is the active enabler for instance cross-links and "Used by" sections.
- Agreed doc structure: page title is the ASDL file name with extension; file-level Overview and Imports live at the document level; module sections render Notes (module-level overview), Interface (name + description), Instances, Nets, and Used by.

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
1. Validate Sphinx render matches agreed document structure; identify remaining mismatches for follow-up.

## Risks / unknowns
- Module name collisions across files must be disambiguated in tooling without exposing hash IDs to users.
- Sphinx link resolution depends on depgraph completeness; unresolved refs should degrade gracefully.
- Sphinx docs builds currently miss `.asdlrc` lib roots unless explicitly wired, leading to AST-010 import errors.
- Manifest auto-expansion must avoid non-deterministic ordering and duplicates across entry imports.
- Current Sphinx output still shows nested/duplicate headings for some files; likely remaining mismatch in document/module section ordering.

## Codebase size snapshot (2026-02-09)
- Measurement unit: non-empty lines of UTF-8 text files.
- Exclusions: `.git/`, `node_modules/`, virtualenv/build cache directories.

### Top-level buckets
- Core ASDL compiler (`src/asdl`): **13,813 LoC** across 65 files.
- Test suite (`tests`): **6,659 LoC** across 54 files.
- IDE extensions (`extensions/asdl-visualizer` + `syntax-highlighter`): **7,762 LoC** across 51 files.
  - Note: extension lockfiles account for ~2,413 LoC; excluding lockfiles yields ~5,349 LoC.

### Core compiler subsystem breakdown (`src/asdl`)
- `docs`: 3,382 LoC
- `core`: 2,395 LoC
- `lowering`: 2,294 LoC
- `emit`: 2,174 LoC
- `ast`: 1,284 LoC
- `patterns_refactor`: 884 LoC
- `cli`: 748 LoC
- `imports`: 387 LoC
- `diagnostics`: 227 LoC

### Test suite subsystem breakdown (`tests`)
- `tests/unit_tests`: 6,227 LoC
- `tests/e2e`: 432 LoC

### IDE extension breakdown
- `extensions/asdl-visualizer`: 6,575 LoC (4,211 LoC excluding `package-lock.json`)
- `syntax-highlighter`: 1,187 LoC (1,138 LoC excluding `package-lock.json`)
