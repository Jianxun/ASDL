# Task summary (DoD + verify)
- DoD: Update the Sphinx project manifest workflow so each entry file expands to the full resolved import graph (entries + imported files). Generated stub pages and the project toctree must include all resolved files in deterministic order, with duplicates removed. Import resolution must use the same lib_roots/.asdlrc handling as depgraph builds. Add unit coverage to assert auto-expansion from a minimal manifest that only lists a top file, and that imported files appear in the generated list. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_pages.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect project manifest parsing and stub generation in Sphinx domain.
- Add import-graph expansion for manifest entries using shared resolver settings.
- Update tests to cover auto-expansion and deterministic ordering.
- Run verify command.

# Progress log
- 
- 2026-02-01 02:20 — Task intake and context review (contract/lessons/tasks/project status); set T-256 to in_progress and linted tasks_state; created feature branch `feature/T-256-sphinx-manifest-expand`; next: inspect Sphinx manifest handling.
- 2026-02-01 02:26 — Added unit test for manifest import expansion; files: tests/unit_tests/docs/test_sphinx_project_pages.py; next: implement manifest expansion in Sphinx domain.
- 2026-02-01 02:26 — Commit c1d005a: add manifest import expansion test.
- 2026-02-01 02:26 — Implemented manifest entry expansion using dependency graph + lib_roots; updated project page generation to pass lib_roots; files: src/asdl/docs/sphinx_domain.py; next: run targeted tests.
- 2026-02-01 02:26 — Commit 4e94d0d: expand Sphinx manifest entries via depgraph.
- 2026-02-01 02:26 — Verification: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_pages.py -v (passed).

# Patch summary
- Added project manifest unit test for import graph expansion.
- Expanded manifest entries using dependency graph resolution with lib_roots and manifest-relative path mapping; project pages now pass lib_roots.

# PR URL
- https://github.com/Jianxun/ASDL/pull/275

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_pages.py -v

# Status request
- Done (ready_for_review)

# Blockers / Questions
- None.

# Next steps
- Open PR, update task state to ready_for_review.
- 2026-02-01 02:34 — Opened PR https://github.com/Jianxun/ASDL/pull/275; next: update tasks_state and lint.
- 2026-02-01 02:34 — Set T-256 status to ready_for_review with PR 275; next: run lint_tasks_state.
- 2026-02-01 02:34 — Ran ./venv/bin/python scripts/lint_tasks_state.py (ok).
- 2026-02-01 02:37 — Review intake: PR 275 targets main, scratchpad and verify logs present; set T-256 to review_in_progress; next: run required tests and scope check.
- 2026-02-01 02:37 — Verification rerun: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_pages.py -v (passed); next: scope review.
- 2026-02-01 02:38 — Scope check complete; changes align with DoD and no out-of-scope docs touched; next: finalize review decision.
- 2026-02-01 02:38 — Review decision: clean; posted PR review comment; next: set status review_clean and begin merge/closeout.
- 2026-02-01 02:38 — Set T-256 status to review_clean and linted tasks_state; next: merge and close out.
- 2026-02-01 02:39 — Set T-256 status to done with merged=true and linted tasks_state; next: commit, push, and merge PR.
