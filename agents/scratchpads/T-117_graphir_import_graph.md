# T-117 Import graph to GraphIR design

## Task summary (DoD + verify)
- DoD: Build GraphIR design from the import graph by converting each document
  with its NameEnv/ProgramDB, preserving entry-file order and file_id metadata.
  Add tests that cover multi-file resolution and unresolved import diagnostics.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_graphir_imports.py -v`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/roles/executor.md
- docs/specs/spec_asdl_graphir.md
- src/asdl/ir/converters/ast_to_graphir.py
- src/asdl/ir/pipeline.py
- tests/unit_tests/ir/test_graphir_converter.py
- tests/unit_tests/parser/test_import_resolution.py

## Plan
- [x] Implement import-graph conversion to GraphIR with ordered file IDs.
- [x] Add tests for multi-file resolution and unresolved import diagnostics.
- [x] Verify with targeted pytest.

## Progress log
- 2026-01-13: Task initialized, status set to in_progress.
- 2026-01-13: Added import-graph conversion, pipeline helper, and tests.
- 2026-01-13: Verified tests/unit_tests/ir/test_graphir_imports.py.

## Patch summary
- Added import-graph conversion with file ordering and cross-file symbol
  resolution in `src/asdl/ir/converters/ast_to_graphir.py`.
- Added GraphIR import graph helper in `src/asdl/ir/pipeline.py`.
- Added import-graph unit tests in `tests/unit_tests/ir/test_graphir_imports.py`.

## PR URL
- https://github.com/Jianxun/ASDL/pull/126

## Verification
- `venv/bin/pytest tests/unit_tests/ir/test_graphir_imports.py -v`

## Status request
- Ready for review.

## Blockers / Questions
- None.

## Next steps
- Reviewer to verify GraphIR import conversion and test coverage.
