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
- [x] Inspect lowering + registry usage for expressions.
- [x] Add kind-aware expression caching + register expr kinds.
- [x] Update lowering tests for cache reuse + kind mapping.
- [x] Run verify command.

# Understanding
Pattern expression IDs should be reused only when the expression string and semantic kind match. The lowering should record expr_id -> kind in registries so downstream passes can distinguish net/instance/endpoint/param expressions. Tests should confirm that repeated expressions reuse IDs and that kinds are recorded correctly.

# Progress log
- 2026-01-23 20:07 — Task intake, read context/contract/tasks, created scratchpad; next: set task status to in_progress, create branch.
- 2026-01-23 20:07 — Set T-207 status to in_progress, ran lint_tasks_state.py; next: create feature branch and commit kickoff changes.
- 2026-01-23 20:07 — Created branch feature/T-207-lowering-expr-kind-cache; next: commit kickoff changes and inspect lowering/tests.
- 2026-01-23 20:07 — Commit 602ed50 chore: start T-207.
- 2026-01-23 20:09 — Added tests for expr cache reuse and kind mapping; files touched: tests/unit_tests/core/test_patterned_graph_lowering.py.
- 2026-01-23 20:09 — Commit 2b51562 test: cover expr cache and kinds.
- 2026-01-23 20:10 — Updated expression registration to cache by (kind, expr) and record expr kinds; files touched: src/asdl/lowering/ast_to_patterned_graph_expressions.py, src/asdl/lowering/ast_to_patterned_graph_instances.py, src/asdl/lowering/ast_to_patterned_graph_nets.py, src/asdl/lowering/ast_to_patterned_graph.py.
- 2026-01-23 20:10 — Commit 64e0509 feat: cache expressions by kind.
- 2026-01-23 20:10 — Ran ./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v (pass).
- 2026-01-23 20:11 — Commit cee9e1b docs: update T-207 scratchpad.
- 2026-01-23 20:11 — Pushed branch feature/T-207-lowering-expr-kind-cache.
- 2026-01-23 20:11 — Opened PR https://github.com/Jianxun/ASDL/pull/213.

# Patch summary
- Added lowering tests to assert expr cache reuse and expr kind mapping.
- Cached expressions by (kind, expression) and registered expr kinds during lowering.

# PR URL
https://github.com/Jianxun/ASDL/pull/213

# Verification
- ./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py -v

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions

# Next steps
- Await review.
- 2026-01-23 20:12 — Set T-207 status to ready_for_review with PR 213; ran lint_tasks_state.py.
