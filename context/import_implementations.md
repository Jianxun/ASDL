# Import System Implementation Snapshot

This file distills the working context for the ASDL import system to avoid re-reading large parts of the codebase between sessions.

## Components and Locations
- src/asdl/elaborator/import_/path_resolver.py: Builds search paths (CLI -> config -> env ASDL_PATH -> defaults). Resolves relative paths to absolute.
- src/asdl/elaborator/import_/file_loader.py: Parses files with caching and circular detection support.
- src/asdl/elaborator/import_/module_resolver.py: Cross-file module lookup utilities.
- src/asdl/elaborator/import_/alias_resolver.py: Validates and helps resolve model_alias (import_alias.module format).
- src/asdl/elaborator/import_/diagnostics.py: Structured E044x error/warning constructors and utilities.
- src/asdl/elaborator/import_/import_resolver.py: Orchestrates Phase 0 import resolution:
  - Parse main file -> load DAG (DFS) -> validate aliases -> flatten/normalize modules.
  - Normalizes instance model refs: strips "alias." prefix and applies model_alias to local names.

## Phase 0 Orchestration (Integrated)
- Wrapper: Elaborator.elaborate_with_imports(main_file_path, search_paths=None, top=None)
  - Calls ImportResolver.resolve_imports(...) -> returns flattened ASDLFile + diagnostics.
  - Applies optional top override.
  - Calls existing Elaborator.elaborate(asdl_file) for pattern and variable phases.

## CLI Integration
- src/asdl/cli/elaborate.py:
  - Uses elaborate_with_imports.
  - Supports --search-path (multiple).
- src/asdl/cli/netlist.py:
  - Uses elaborate_with_imports before validate -> generate.
  - Supports --search-path (multiple).

## Data Structures
- ASDLFile.imports: Dict[str, str] — alias: path/to/file.asdl
- ASDLFile.model_alias: Dict[str, str] — local: import_alias.module
- Module.instances hold Instance with model ref. After Phase 0, instance models are normalized to local module names.

## Current Behavior Guarantees
- Depth-first dependency loading with circular detection.
- First-match wins path resolution; deterministic search path order.
- Flattened output preserves main file metadata; modules are combined; instance model names normalized for downstream passes.

## Known Gaps (Next Phase Targets)
- Enforce E0443/E0444 for unresolved/invalid instance models post-flatten.
- Warnings for unused imports and unused model_alias entries.
- Prune unreachable modules based on top_module/--top; deterministic module order.
- Improve file-not-found diagnostics with explicit probe paths.
- Optional config file support to merge search paths (CLI -> config -> env -> defaults).

## Example Fixture
- examples/imports/toy/: primitives.asdl, opamp.asdl, top.asdl (netlists to top.spice).
  - Run: asdlc netlist examples/imports/toy/top.asdl --search-path examples/imports/toy --top top_amp

## Test References
- tests/integration/test_import_orchestration_toy.py: Passing integration test covering Phase 0 normalization and netlisting on toy.
- Unit tests for import subsystems under tests/unit_tests/elaborator/import_/.

## Quick API Reminders
- ImportResolver.resolve_imports(main_file_path: Path, search_paths: Optional[List[Path]]) -> Tuple[Optional[ASDLFile], List[Diagnostic]]
- PathResolver.get_search_paths(cli_paths=None, config_paths=None) -> List[Path]
- Elaborator.elaborate(asdl_file) -> (ASDLFile, diagnostics)
- Elaborator.elaborate_with_imports(main_file_path, search_paths=None, top=None) -> (ASDLFile, diagnostics)
