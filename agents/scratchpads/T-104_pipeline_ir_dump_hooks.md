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
- [ ] Update task state + branch; outline subtasks.
- [ ] Add pipeline debug options and wire to dump stages.
- [ ] Add pipeline dump tests for NFIR/IFIR/atomized IFIR.
- [ ] Run verify.

# Progress log
- 2026-01-12: Initialized scratchpad.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
