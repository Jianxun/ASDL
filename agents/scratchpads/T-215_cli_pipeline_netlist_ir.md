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

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
# Progress log
- 2026-01-24 02:25 — Task intake: reviewed contract/tasks/project status and created scratchpad; set T-215 to in_progress; next step inspect CLI/lowering entrypoints.
- 2026-01-24 02:25 — Created feature branch feature/T-215-cli-netlist-ir; next step scan CLI pipeline for IFIR usage.
- 2026-01-24 02:32 — Added NetlistIR pipeline helper and updated CLI netlist command to use it; files: src/asdl/lowering/__init__.py, src/asdl/cli/__init__.py; next step update specs.
