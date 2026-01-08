# T-076 Import-aware MVP pipeline

## Task summary
- **DoD**: Extend `run_mvp_pipeline` to accept an entry file path and optional `--lib` roots, resolve the import graph, and lower all loaded documents into a single NFIR design. Ignore `top` declarations from non-entry files; use only the entry file's `top` when building the design. Abort the pipeline on any error-severity diagnostics from import resolution or lowering, but allow warnings to flow through. Preserve the existing document-only behavior for single-file callers. Add e2e tests that exercise import-aware pipeline success and import failure gating.
- **Verify**: `pytest tests/unit_tests/e2e -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/ir/pipeline.py`
- `src/asdl/imports/resolver.py`
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/cli/__init__.py`
- `tests/unit_tests/e2e/test_pipeline_mvp.py`

## Plan
1. Extend pipeline entrypoint to resolve import graph and build a merged NFIR design.
2. Ensure non-entry `top` is ignored; use entry `top` only.
3. Add e2e coverage for import-aware success and import-error gating.

## Todo
- [x] Add import-aware pipeline path with error gating.
- [x] Preserve single-file document-only behavior.
- [x] Add e2e tests for import success/failure cases.

## Progress log
- Added import-graph e2e tests for success and missing-import failure.
- Extended pipeline to resolve imports, merge NFIR designs, and gate on errors.

## Patch summary
- Added import-aware lowering and error gating in `run_mvp_pipeline`.
- Added e2e import-graph coverage for success and missing-import failure.

## PR URL
- https://github.com/Jianxun/ASDL/pull/77

## Verification
- `./venv/bin/pytest tests/unit_tests/e2e -v`

## Status request (Done / Blocked / In Progress)
- Done

## Next steps
- Await review feedback.

## Blockers / Questions
- None.
