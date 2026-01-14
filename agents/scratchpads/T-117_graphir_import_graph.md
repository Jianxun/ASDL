# T-117 Import graph to GraphIR design

## Goal
- Build GraphIR design from import graph with per-document conversion using
  NameEnv/ProgramDB, preserving entry-file order and file_id metadata.
- Add tests for multi-file resolution and unresolved import diagnostics.

## Context
- DoD: Build a GraphIR design from the import graph by converting each document
  with its NameEnv/ProgramDB, preserving entry-file order and file_id metadata.
  Add tests that cover multi-file resolution and unresolved import diagnostics.
- Verify: `venv/bin/pytest tests/unit_tests/ir/test_graphir_imports.py -v`

## Plan
- Review current AST->GraphIR converter and pipeline import handling.
- Implement import-graph conversion to GraphIR design with ordered file_ids.
- Add/adjust tests for multi-file imports and diagnostics.
- Verify with targeted pytest.

## Notes
- 

## Progress
- 2026-??-??: Task initialized, status set to in_progress.
