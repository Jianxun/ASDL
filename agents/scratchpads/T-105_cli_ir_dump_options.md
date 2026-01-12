# Task summary (DoD + verify)
- Add asdlc netlist flags to dump NFIR/IFIR/atomized IFIR to disk (for example, --dump-ir nfir,ifir,atom and --dump-dir). Use pipeline debug hooks to emit dumps next to the output file by default. Update CLI help text and document file naming conventions.
- Verify: pytest tests/unit_tests/e2e/test_pipeline_mvp.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- src/asdl/cli/__init__.py
- src/asdl/ir/pipeline.py

# Plan
- [ ] Update task state + branch; outline subtasks.
- [ ] Add CLI flags and map to pipeline debug options.
- [ ] Document dump naming conventions in CLI help.
- [ ] Run verify.

# Progress log
- 2026-01-12: Initialized scratchpad.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
