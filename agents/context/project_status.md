# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- ASDL docs pipeline is focused on Sphinx (Tier 2); Markdown generation is deprecated.
- Comment-based docstring extraction is implemented per ADR-0021 and feeds Sphinx rendering.
- Doc rendering targets per-file `asdl:document` pages plus project-level manifest wiring.
- Dependency graph support is the active enabler for instance cross-links and "Used by" sections.
- Agreed doc structure: page title is the ASDL file name with extension; file-level Overview and Imports live at the document level; module sections render Notes (module-level overview), Interface (name + description), Instances, Nets, and Used by.
- ASDL authoring ergonomics work is now scoped to a fresh extension package at `extensions/asdl-language-tools/` with a dedicated spec and ADR.
- Instance parameter schema evolution is now accepted in ADR-0031: keep inline shorthand (with quote-aware parsing) and add structured instance objects with canonical `parameters`.
- Post-merge review found a regression where structured instance declarations can raise a raw exception during AST-to-PatternedGraph lowering instead of emitting diagnostics.
- View-binding task wave T-287..T-296 is merged and archived.
- Re-evaluation found two remaining defects after the merged fixes:
  import-qualified refs (`ns.symbol`) are currently rejected by the new
  module-symbol validator, and occurrence-specific path overrides can fail for
  reused module definitions due to non-uniform rewrite constraints.

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
1. T-297: restore import-qualified refs while preserving decorated-symbol validation.
2. T-298: support occurrence-specific view application for reused module definitions.
3. Execute T-297/T-298 with embedded self-contained regression updates (per contract convention).

## Risks / unknowns
- Module name collisions across files must be disambiguated in tooling without exposing hash IDs to users.
- Sphinx link resolution depends on depgraph completeness; unresolved refs should degrade gracefully.
- Sphinx docs builds currently miss `.asdlrc` lib roots unless explicitly wired, leading to AST-010 import errors.
- Manifest auto-expansion must avoid non-deterministic ordering and duplicates across entry imports.
- Current Sphinx output still shows nested/duplicate headings for some files; likely remaining mismatch in document/module section ordering.
- Python worker runtime/discovery across local dev environments may introduce startup friction for extension users.
- Dual instance authoring forms can drift if helper parsers diverge; lowering currently has a structured-instance crash path until T-285 lands.
- Until T-297 lands, valid import-qualified refs in instance expressions are blocked by parse validation.
- Until T-298 lands, path-scoped divergent binding can error on shared module definitions instead of emitting per-occurrence realized refs.
