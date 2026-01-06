# T-062 Import Resolution

## Task summary
- DoD: Implement import resolution + file loading per `docs/specs/spec_asdl_import.md` (relative/absolute/logical roots, no extension inference, `--lib` name ignored for resolution, path normalization collapses `.`/`..`, no symlink resolution). Build a `ProgramDB` keyed by `file_id` (absolute path) and a per-file `NameEnv` that allows multiple namespaces to the same file. Detect cycles with a readable import chain and emit diagnostics for missing files and malformed paths. Add unit tests for resolution order, cycles, and missing imports.
- Verify: `pytest tests/unit_tests/parser -v && pytest tests/unit_tests/ir -v`

## Read
- `docs/specs/spec_asdl_import.md`
- `src/asdl/ast/parser.py`
- `src/asdl/ir/pipeline.py`
- `src/asdl/imports/` (new package)
- `tests/unit_tests/parser/`
- `tests/unit_tests/ir/`

## Proposed module layout
- `src/asdl/imports/resolver.py`: resolve paths, build import graph, load ASTs.
- `src/asdl/imports/program_db.py`: global symbol registry keyed by `file_id`.
- `src/asdl/imports/name_env.py`: per-file namespace map (`ns -> file_id`).
- `src/asdl/imports/diagnostics.py`: import-stage diagnostic helpers/codes.

## Plan
- Implement path resolution with ordered roots and absolute-path normalization.
- Build an import graph with cycle detection and readable chains.
- Parse each imported file with existing AST parser; collect diagnostics.
- Populate `ProgramDB` and `NameEnv` per file.
- Add tests for resolution order, missing import, and cycle errors.

## Progress log
- Initialized scratchpad.

## Patch summary
- TBD.

## Verification
- TBD.

## Blockers / Questions
- None.

## Next steps
- Implement resolver + ProgramDB and add tests.
