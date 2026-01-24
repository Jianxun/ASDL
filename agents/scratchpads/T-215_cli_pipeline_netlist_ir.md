# Task summary (DoD + verify)
- DoD: Update CLI and pipeline entrypoints to build NetlistIR and emit from it, removing IFIR/xDSL dependencies in the refactor path. Keep legacy flags (if any) isolated. Update specs that describe the compiler stack and netlist emission inputs to reference NetlistIR.
- Verify: venv/bin/pytest tests/unit_tests/cli -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect CLI/lowering entrypoints and netlist emission specs for IFIR references.
- Update pipeline to produce NetlistIR, keep legacy flags isolated.
- Update docs/specs for compiler stack + netlist emission inputs.
- Add/adjust tests if required; run CLI unit tests.

# Progress log
- 2026-01-24 02:25 — Task intake: reviewed contract/tasks/project status and created scratchpad; set T-215 to in_progress; next step inspect CLI/lowering entrypoints.
- 2026-01-24 02:25 — Created feature branch feature/T-215-cli-netlist-ir; next step scan CLI pipeline for IFIR usage.
- 2026-01-24 02:32 — Added NetlistIR pipeline helper and updated CLI netlist command to use it; files: src/asdl/lowering/__init__.py, src/asdl/cli/__init__.py; next step update specs.
- 2026-01-24 02:32 — Commit cc53094: add NetlistIR pipeline helper and switch CLI netlist command; next step update specs.
- 2026-01-24 02:33 — Updated compiler stack and netlist emission specs to reference NetlistIR; files: docs/specs/spec_compiler_stack.md, docs/specs/spec_netlist_emission.md; next step commit docs and run tests.
- 2026-01-24 02:33 — Commit b422fa0: update compiler stack and netlist emission specs for NetlistIR; next step run CLI unit tests.
- 2026-01-24 02:34 — Verification: venv/bin/pytest tests/unit_tests/cli -v (pass).
- 2026-01-24 02:36 — PR created: https://github.com/Jianxun/ASDL/pull/225; next step update task state.
- 2026-01-24 02:37 — Set T-215 status to ready_for_review (PR 225) and ran scripts/lint_tasks_state.py.

# Patch summary
- Added NetlistIR pipeline helper and switched CLI netlist to use it.
- Updated compiler stack and netlist emission specs to reference NetlistIR.

# PR URL
- https://github.com/Jianxun/ASDL/pull/225

# Verification
- venv/bin/pytest tests/unit_tests/cli -v

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None.

# Next steps
- Await review.
