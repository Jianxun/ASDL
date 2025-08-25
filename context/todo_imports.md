# ASDL Import System – Import Phase Todos

## Current Status
- Phase 1.2 MVP complete; enhancements through 1.2.6 shipped (2025-08-25)
- Core components integrated; CLI supports `--search-path`; diagnostics E0441–E0445 active
- Quality warnings added: I0601 (unused import), I0602 (unused model_alias)

## Recent Enhancements
- E0443/E0444 post-load validation of qualified instance references
- E0441 includes explicit probe paths
- CLI netlist gated: generation skipped when ERROR diagnostics exist
- Unit tests updated; CLI toy integration test scaffolded

## Remaining Work
- Config file support for search paths (asdl.config.yaml)
- Additional integration tests (toy variants, transitive scenarios)
- Prune unreachable modules based on top/--top; deterministic module order
- Documentation: user guide, import tutorial, ASDL_PATH best practices

## Tests
- Unit: E0443/E0444 reference validation
- Unit: E0441 probe paths in missing import diagnostics
- Unit: Alias resolver validations and collisions
- Integration: CLI toy netlist (complete and extend)

## Notes
- Simplicity-first: direct file path imports; ASDL_PATH resolution
- Model names normalized during flattening; aliases applied pre-elaboration