## ASDL Import System

This document describes the import-resolution phase in the Elaborator: its pipeline, orchestration, key design decisions, and their rationales.

## Goals
- Resolve imports across one or more `.asdl` files into a single, flattened `ASDLFile` for downstream passes.
- Provide clear, actionable diagnostics (E-codes) for all failure modes.
- Keep behavior predictable and transparent (probe order, precedence, cycle detection).

## Pipeline
1) Parse main file
   - Component: `ASDLParser`
   - Output: `ASDLFile` (main), parse diagnostics

2) Determine search roots
   - Component: `PathResolver`
   - Policy: environment-only roots from `ASDL_PATH` (POSIX `:`, Windows `;`) with fallback to current working directory `[Path.cwd()]` when unset.
   - Per-import rule: prepend the importing file’s directory to the effective search roots.

3) Build dependency graph & load files
   - Component: `DependencyGraphBuilder` (uses `PathResolver`, `FileLoader`)
   - Output:
     - `ImportGraph` (nodes = files, edges = imports)
     - `AliasResolutionMap` (file → {alias → absolute path | None})
     - `loaded_files` keyed by absolute `Path`
   - Behavior:
     - For each import, probe candidates across effective roots: `[dir(importing_file)] + ASDL_PATH + [cwd fallback]`.
     - If 0 candidates: E0441 (Not Found) including the exact probe list.
     - If >1 candidates: E0447 (Ambiguous Import Resolution) listing all matches; resolution is blocked for that alias.
     - Exactly 1 candidate: load via `FileLoader`.
     - Cycle detection is centralized in `FileLoader` (E0442).
     - Load/parse failures are E0446.

4) Validate references and model_alias
   - Component: `ReferenceValidator` (delegates alias semantics to `AliasResolver`)
   - Checks:
     - Qualified instance references `alias.module`:
       - E0444 when `alias` is unknown in the importing file.
       - E0443 when `module` is not found in the referenced file.
     - `model_alias` definitions:
       - E0444 for invalid qualified format or unknown import alias.
       - E0445 when a `model_alias` name collides with an import alias.
     - Tracks alias usage correctly (fixed loop scoping). Optional unused warnings (`E0601`/`E0602`) may be toggled later.

5) Flatten modules
   - Component: `Flattener`
   - Steps:
     - Rewrite instance model names: strip `alias.` prefix; apply per-file `model_alias` indirection.
     - Merge modules from imports into the main file based on precedence policy.
     - Default precedence: LocalWins (local module keeps; imported conflicting name triggers a shadowing warning).
     - Optional: drop `imports`/`model_alias` metadata via `FlattenOptions`.
   - Note: Deterministic sorting of traversal and module names is intentionally not enabled at this time.

## Orchestration
- High-level entry point: `ImportCoordinator` orchestrates stages 2–5 after parsing.
- Backwards compatibility: `ImportResolver` is a thin wrapper that delegates to `ImportCoordinator`.
- Supporting modules:
  - `path_resolver.py`: compute roots; build probe lists.
  - `file_loader.py`: cache loads, emit E0441/E0442/E0446; normalize to absolute paths.
  - `dependency_graph.py`: build graph + alias map; call loader; detect ambiguity.
  - `reference_validator.py` + `alias_resolver.py`: reference and alias checks.
  - `flattener.py`: rewrite/merge with precedence.
  - `diagnostics.py`: structured diagnostic constructors.
  - `tracing.py`: centralized logging of paths, probes, alias maps, merge conflicts.

## Design Decisions & Rationales
- ASDL_PATH-only with fallback to cwd
  - Rationale: Simple mental model; environment drives shared library roots. Fallback supports quick trials.

- Importer-relative resolution (prepend `dir(importing_file)` per import)
  - Rationale: Self-contained IPs that use relative paths work without `ASDL_PATH` tweaks; portable across file moves.

- Ambiguity is a hard error (E0447)
  - Rationale: First-match-wins can silently select the wrong library; in IC design this is dangerous. Listing all matches prompts explicit disambiguation.

- Absolute-path identity and alias map
  - Rationale: Avoid mismatches between raw strings and resolved paths; stable keys for caches and validation.

- LocalWins precedence with shadowing warning
  - Rationale: Local file is the user’s active work; imported libraries should not override it silently.

- Single-source cycle detection in `FileLoader`
  - Rationale: One authoritative place eliminates duplicated/contradictory cycle logic.

- Determinism (sorting) intentionally skipped (for now)
  - Rationale: Keep scope focused on correctness and diagnostics; can add sorted traversal later if needed.

## Diagnostics
- E0441: Import file not found (includes probe candidates)
- E0442: Circular import detected
- E0443: Module not found in imported file
- E0444: Import alias not found
- E0445: Model alias collides with import alias
- E0446: Import file load/parse failure
- E0447: Ambiguous import resolution (multiple matching files)
- E0448: Invalid qualified reference format (e.g., bad 'alias.module')
- E0601/E0602: Style warnings (e.g., shadowing, unused) — gated as needed

## Logging & Tracing
- DEBUG: phase progress, search paths, loads, timings
- TRACE (fallback to DEBUG if unavailable): per-import probe lists, alias maps, cycle stacks, precedence conflicts

## Usage
```python
from pathlib import Path
from src.asdl.elaborator.import_ import ImportCoordinator, PrecedencePolicy, FlattenOptions

coordinator = ImportCoordinator(
    precedence=PrecedencePolicy.LOCAL_WINS,
    flatten_options=FlattenOptions(drop_metadata=False),
)

flattened, diagnostics = coordinator.resolve_imports(Path("path/to/main.asdl"))
```

Backward-compatible wrapper:
```python
from src.asdl.elaborator.import_ import ImportResolver

resolver = ImportResolver()
flattened, diagnostics = resolver.resolve_imports(Path("path/to/main.asdl"))
```

## Testing
- Unit tests cover: path resolution, ambiguity vs. not-found, cycles, qualified references, alias validation, flattening precedence.
- All elaborator unit tests must pass before integration changes.


