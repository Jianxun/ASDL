# T-118 Pipeline switch to GraphIR

## Task summary (DoD + verify)
- Switch MVP pipeline to AST/imports -> GraphIR -> IFIR -> emit.
- Add a GraphIR verification pass.
- Wire CLI/pipeline entry points and update the E2E pipeline fixture.
- Verify with `venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py -v`.

## Read
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/ir/pipeline.py
- src/asdl/cli/__init__.py
- src/asdl/ir/converters/ast_to_graphir.py
- tests/unit_tests/e2e/test_pipeline_mvp.py

## Plan
- TODO:
  - [x] Update E2E pipeline fixture assertions for GraphIR metadata.
  - [x] Switch pipeline to GraphIR (converter + verify + IFIR projection).
  - [x] Wire CLI/pipeline entry points if needed.
  - [x] Run E2E verification and capture results.
  - [x] Close out scratchpad + task state, open PR.

## Progress log
- 2026-01-13: Started task, set status to in_progress.
- 2026-01-13: Updated E2E fixture assertion for entry file IDs.
- 2026-01-13: Switched pipeline to GraphIR with verify pass + IFIR projection.
- 2026-01-13: Added GraphIR backend + source annotation conversion for emit spans.
- 2026-01-13: E2E pipeline tests passing.

## Patch summary
- Switched MVP pipeline to GraphIR with verification and IFIR projection.
- Preserved GraphIR device backends and instance source annotations for emission.
- Updated E2E pipeline fixture to assert entry file metadata.

## PR URL
- https://github.com/Jianxun/ASDL/pull/127

## Verification
- `venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py -v`

## Status request (Done / Blocked / In Progress)
- Done.

## Blockers / Questions
- None.

## Next steps
- Await review feedback.
