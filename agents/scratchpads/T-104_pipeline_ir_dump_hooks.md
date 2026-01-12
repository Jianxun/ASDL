# Task summary (DoD + verify)
- Add debug options to the MVP pipeline to dump NFIR/IFIR/atomized IFIR modules to text for inspection. Support selecting stages and directing output to a dump directory or callback; ensure dumps are emitted even when verify is disabled. Add unit tests that run the pipeline on a small fixture and assert the dump outputs exist and include expected op headers.
- Verify: pytest tests/unit_tests/e2e/test_pipeline_mvp.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/ir/pipeline.py
- tests/unit_tests/e2e/test_pipeline_mvp.py

# Plan
- [x] Update task state + branch; outline subtasks.
- [x] Add pipeline dump tests for NFIR/IFIR/atomized IFIR.
- [x] Add pipeline debug options and wire to dump stages.
- [x] Run verify.

# Progress log
- 2026-01-12: Initialized scratchpad.
- 2026-01-12: Added IR dump tests and pipeline dump hooks with stage selection.
- 2026-01-12: Opened PR #117.

# Patch summary
- Added pipeline dump options, stage constants, and dump pass hooks.
- Added end-to-end tests for dump directory and callback outputs.

# PR URL
- https://github.com/Jianxun/ASDL/pull/117

# Verification
- ./venv/bin/pytest tests/unit_tests/e2e/test_pipeline_mvp.py -v

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions

# Next steps
