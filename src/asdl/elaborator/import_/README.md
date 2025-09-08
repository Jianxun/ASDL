## ASDL Import System (Elaborator Phase)

This package implements the import-resolution phase of the Elaborator. It discovers and loads imported `.asdl` files, validates cross-file references, and produces a flattened `ASDLFile` for downstream passes.

## High-level flow
- Parse main file
- Resolve search paths from `ASDL_PATH` (fallback `["."]`)
- Build dependency graph and load imports
- Validate qualified references and model aliases
- Flatten modules into a single `ASDLFile`

## Modules and responsibilities
- `path_resolver.py`
  - Resolves effective search roots from environment `ASDL_PATH` (fallback `["."]`).
  - Provides `resolve_file_path()` and `get_probe_paths()`.

- `file_loader.py`
  - Loads `.asdl` files with a cache and circular-detection using a loading stack.
  - Diagnostics: `E0441` (not found), `E0446` (load/parse failure), `E0442` (circular).
  - Normalizes paths to absolute for identity and cache consistency.

- `types.py`
  - `ImportGraph`, `GraphNode`, and `AliasResolutionMap` (file → alias → resolved path or `None`).

- `policies.py`
  - `PrecedencePolicy` (`LOCAL_WINS` | `IMPORT_WINS`).
  - `FlattenOptions` (e.g., `drop_metadata`).

- `dependency_graph.py`
  - `DependencyGraphBuilder` constructs the import graph and `AliasResolutionMap`.
  - Uses `PathResolver` for path resolution and `FileLoader` for loading; relies on the loader for cycle detection.

- `reference_validator.py`
  - `ReferenceValidator` checks qualified instance references and delegates model-alias checks to `AliasResolver`.
  - Emits `E0443` (module not found in import), `E0444` (unknown import alias), `E0448` (invalid qualified reference format).
  - Fixes alias-usage tracking to avoid the prior loop scoping bug.

- `flattener.py`
  - `Flattener` merges modules and rewrites instance model names:
    - Strips import alias prefixes (`alias.mod → mod`).
    - Applies per-file `model_alias` indirections.
    - Merge precedence configurable via `PrecedencePolicy` (default: local wins with a warning).
    - Optionally drops `imports` and `model_alias` via `FlattenOptions`.
  - Warning on conflict when `LOCAL_WINS`: currently uses an `E0601`-coded warning.

- `coordinator.py`
  - `ImportCoordinator` orchestrates the full flow and is the new high-level entry point.

- `import_resolver.py`
  - Backwards-compatible wrapper that exposes the old `ImportResolver` API and delegates to `ImportCoordinator`.

- `alias_resolver.py`
  - Shared logic for validating and resolving `model_alias` targets.

- `module_resolver.py`
  - Utility for three-step module lookup (local → model_alias → qualified). Kept for compatibility and potential reuse.

- `diagnostics.py`
  - Structured constructors for import-related diagnostics (`E0441–E0448`, `E0601/E0602`).

- `tracing.py`
  - Centralized logging helpers (search paths, probe candidates, alias maps, merge conflicts).

## Data flow between modules
1. `ImportCoordinator` parses the main file (via `ASDLParser`).
2. `DependencyGraphBuilder` builds graph, returns `ImportGraph`, `AliasResolutionMap`, and `loaded_files` keyed by absolute paths.
3. `ReferenceValidator` validates qualified references and model aliases using the alias map and loaded files.
4. `Flattener` rewrites instance models and applies merge policy to produce a flattened `ASDLFile`.

## Diagnostics overview
- `E0441` Import file not found (includes probe candidates).
- `E0442` Circular import detected (from `FileLoader`).
- `E0443` Module not found in imported file.
- `E0444` Import alias not found or invalid alias reference format.
- `E0445` Model alias collides with import alias.
- `E0446` Import file load/parse failure.
- `E0601/E0602` Style warnings (currently: conflict/shadowing uses an `E0601` warning).

## Configuration
- Search paths: set `ASDL_PATH` (colon-separated on POSIX, semicolon on Windows). Fallback is current directory.
- Merge policy: choose `PrecedencePolicy` (defaults to `LOCAL_WINS`).
- Flatten options: enable `FlattenOptions(drop_metadata=True)` to drop `imports`/`model_alias` in output.

## Usage examples
```python
from pathlib import Path
from src.asdl.elaborator.import_ import ImportCoordinator, PrecedencePolicy, FlattenOptions

coordinator = ImportCoordinator(
    precedence=PrecedencePolicy.LOCAL_WINS,
    flatten_options=FlattenOptions(drop_metadata=False),
)

flattened, diagnostics = coordinator.resolve_imports(Path("path/to/main.asdl"))
```

Backward-compatible entry point:
```python
from src.asdl.elaborator.import_ import ImportResolver

resolver = ImportResolver()
flattened, diagnostics = resolver.resolve_imports(Path("path/to/main.asdl"))
```

## Notes
- Deterministic sorting of files/modules is intentionally not enabled at this time (by request); iteration order follows Python dict semantics.
- Cycle detection is single-sourced in `FileLoader`.
- `loaded_files` and alias resolutions use absolute paths for identity consistency.


