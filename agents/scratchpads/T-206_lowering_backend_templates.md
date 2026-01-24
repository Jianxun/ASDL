# Task summary (DoD + verify)
- DoD: Update AST -> PatternedGraph lowering to register device backend templates for each device definition (including imported devices). Add/adjust lowering tests to assert templates are present in registries.
- Verify: venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect AST -> PatternedGraph lowering path and registry usage.
- Add backend template registration for device definitions, including imported devices.
- Update lowering tests to assert device backend templates registry entries.
- Run verify command.

# Understanding
AST -> PatternedGraph lowering should collect backend template metadata from device definitions (local and imported) and register them in the PatternedGraph registries so downstream passes can access templates. Tests in patterned graph lowering should assert the registry includes expected template values.

# Progress log
- 2026-01-23 19:56 — Task intake, read context/contract/tasks, created scratchpad; next: set task status in_progress, create branch, inspect lowering + tests.
- 2026-01-23 19:56 — Set T-206 status to in_progress, ran lint_tasks_state; next: create feature branch and commit kickoff changes.
- 2026-01-23 19:56 — Created branch feature/T-206-lowering-backend-templates; next: commit kickoff changes and inspect lowering + tests.
- 2026-01-23 19:56 — Commit 5caa415 chore: start T-206.
- 2026-01-23 19:57 — Updated lowering tests to assert device backend templates registry entries; files touched: tests/unit_tests/core/test_patterned_graph_lowering.py.
- 2026-01-23 19:57 — Registered backend templates during device lowering; files touched: src/asdl/lowering/ast_to_patterned_graph.py.
- 2026-01-23 19:57 — Commit de89fdd feat: register device backend templates.
- 2026-01-23 19:58 — Ran ./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v (pass).
- 2026-01-23 19:58 — Commit 16a7d9f docs: update T-206 scratchpad.

# Patch summary
- Registered device backend templates during AST -> PatternedGraph device lowering.
- Added lowering tests asserting device backend template registries for local and imported devices.

# PR URL

# Verification
- ./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions

# Next steps
