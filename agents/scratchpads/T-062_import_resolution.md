# T-062 Import Resolution

## Task summary
- DoD: Implement import resolution + file loading per `docs/specs/spec_asdl_import.md` (relative/absolute/logical roots, no extension inference, `--lib` name ignored for resolution, `ASDL_LIB_PATH` roots, `~`/`$VAR` expansion, path normalization collapses `.`/`..`, no symlink resolution, error on ambiguous logical-path matches with an ordered match list `AST-015`). Build a `ProgramDB` keyed by `file_id` (absolute path) and a per-file `NameEnv` that allows multiple namespaces to the same file. Detect cycles with a readable import chain and emit diagnostics for missing files and malformed paths (`AST-010`/`AST-011`/`AST-012`/`AST-013`/`AST-014`). Add unit tests for resolution order, cycles, missing imports, duplicate symbols in a file, and deduping the same `file_id` across paths.
- Verify: `./venv/bin/pytest tests/unit_tests/parser -v` and `./venv/bin/pytest tests/unit_tests/ir -v`

## Read
- `docs/specs/spec_asdl_import.md`
- `src/asdl/ast/parser.py`
- `src/asdl/ir/pipeline.py`
- `src/asdl/imports/`
- `tests/unit_tests/parser/test_import_resolution.py`
- `tests/unit_tests/ir/`

## Proposed module layout
- `src/asdl/imports/resolver.py`: resolve paths, build import graph, load ASTs.
- `src/asdl/imports/program_db.py`: global symbol registry keyed by `file_id`.
- `src/asdl/imports/name_env.py`: per-file namespace map (`ns -> file_id`).
- `src/asdl/imports/diagnostics.py`: import-stage diagnostic helpers/codes.

## Plan
- Implement path resolution with ordered roots, env expansion, and normalization.
- Build an import graph with cycle detection and readable chains.
- Parse each imported file with existing AST parser; collect diagnostics.
- Populate `ProgramDB` and `NameEnv` per file, deduping identical `file_id`s.
- Add tests for resolution order, missing import, cycle errors, duplicate symbols, and dedupe behavior.

## Progress log
- Initialized scratchpad.
- Implemented import diagnostics, ProgramDB/NameEnv, and resolver with cycle detection/path resolution.
- Added import resolution unit tests and verified parser/IR suites.

## Patch summary
- `src/asdl/imports/diagnostics.py`: added import diagnostics helpers and codes.
- `src/asdl/imports/name_env.py`: implemented per-file namespace bindings.
- `src/asdl/imports/program_db.py`: implemented ProgramDB with duplicate symbol checks.
- `src/asdl/imports/resolver.py`: implemented import resolution, cycle detection, path normalization, and ASDL_LIB_PATH handling.
- `src/asdl/imports/__init__.py`: exported resolver and data structures.
- `tests/unit_tests/parser/test_import_resolution.py`: added import resolution coverage (ambiguous paths, cycles, missing imports, duplicates, dedupe).

## Verification
- `./venv/bin/pytest tests/unit_tests/parser -v`
- `./venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Ready for Review.

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
