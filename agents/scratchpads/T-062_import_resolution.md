# T-062 Import Resolution

## Task summary
- DoD: Implement import resolution + file loading per `docs/specs/spec_asdl_import.md` (relative/absolute/logical roots, no extension inference, `--lib` name ignored for resolution, path normalization collapses `.`/`..`, no symlink resolution). Build a `ProgramDB` keyed by `file_id` (absolute path) and a per-file `NameEnv` that allows multiple namespaces to the same file. Detect cycles with a readable import chain and emit diagnostics for missing files and malformed paths. Add unit tests for resolution order, cycles, missing imports, duplicate symbols in a file, and deduping the same `file_id` across paths.
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
- Add tests for resolution order, missing import, cycle errors, duplicate symbols, and file_id dedupe.

## Progress log
- Initialized scratchpad and reviewed import spec/AST parser/pipeline.
- Implemented import resolver, ProgramDB/NameEnv, and diagnostics helpers.
- Added parser unit tests for resolution order, cycles, missing imports, duplicate symbols, and file_id dedupe.
- Ran parser and IR unit tests.
- Opened PR https://github.com/Jianxun/ASDL/pull/55.

## Patch summary
- Implemented import resolution primitives (`ProgramDB`, `NameEnv`, resolver, diagnostics).
- Added parser tests for import resolution behaviors.

## Verification
- `./venv/bin/pytest tests/unit_tests/parser -v`
- `./venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Ready for review.

## Blockers / Questions
- None.

## Next steps
- Await review.
