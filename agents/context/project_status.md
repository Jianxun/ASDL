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
1. T-281: propagate `module.variables` through PatternedGraph/AtomizedGraph so substitution inputs are preserved.
2. T-282: implement `{var}` substitution in instance parameters with `IR-012`/`IR-013` diagnostics.
3. T-283: add end-to-end regression/diagnostic coverage for module variable substitution.

## Risks / unknowns
- Module name collisions across files must be disambiguated in tooling without exposing hash IDs to users.
- Sphinx link resolution depends on depgraph completeness; unresolved refs should degrade gracefully.
- Sphinx docs builds currently miss `.asdlrc` lib roots unless explicitly wired, leading to AST-010 import errors.
- Manifest auto-expansion must avoid non-deterministic ordering and duplicates across entry imports.
- Current Sphinx output still shows nested/duplicate headings for some files; likely remaining mismatch in document/module section ordering.
- Python worker runtime/discovery across local dev environments may introduce startup friction for extension users.
- Dual instance authoring forms can drift if helper parsers (lowering/docs/completion) diverge; shared normalization and tests are required.
- Module `variables` are currently parsed but not applied in active lowering; placeholders can leak into emitted netlists until T-281..T-283 land.
