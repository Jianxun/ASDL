# Task summary (DoD + verify)
- DoD: Implement pattern expression caching keyed by (kind, expression) during AST -> PatternedGraph lowering so repeated expressions reuse expr_id. Record expr_id -> kind in the registries and add tests covering cache reuse and kind mapping.
- Verify: venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect AST -> PatternedGraph expression registration and registries.
- Add kind-aware cache keys and record expr kind in builder registries.
- Update lowering tests to cover cache reuse and expr kind mapping.
- Run verify command.

# Todo
- [ ] Inspect lowering + registry usage for expressions.
- [ ] Add kind-aware expression caching + register expr kinds.
- [ ] Update lowering tests for cache reuse + kind mapping.
- [ ] Run verify command.

# Understanding
Pattern expression IDs should be reused only when the expression string and semantic kind match. The lowering should record expr_id -> kind in registries so downstream passes can distinguish net/instance/endpoint/param expressions. Tests should confirm that repeated expressions reuse IDs and that kinds are recorded correctly.

# Progress log

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
- 2026-01-23 20:07 — Task intake, read context/contract/tasks, created scratchpad; next: set task status to in_progress, create branch.
- 2026-01-23 20:07 — Set T-207 status to in_progress, ran lint_tasks_state.py; next: create feature branch and commit kickoff changes.
- 2026-01-23 20:07 — Created branch feature/T-207-lowering-expr-kind-cache; next: commit kickoff changes and inspect lowering/tests.
