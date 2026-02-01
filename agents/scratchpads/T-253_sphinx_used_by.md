# Task summary (DoD + verify)
- Extend the docutils renderer to link instance refs to module definitions when resolvable.
- Emit a "Used by" section listing parent modules based on the dependency graph.
- Use graph lookups from the Sphinx env and degrade to plain text when unresolved.
- Anchor targets should use `module_id`; display module names without hash.
- When collisions are present in the current page scope, disambiguate with the relative file path (not the hash).
- Add unit coverage for links and used-by rendering.
- Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).

Verify:
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render_used_by.py -v

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- [x] Add unit tests for instance links, used-by section, and disambiguation.
- [x] Wire dependency graph into Sphinx env and update renderer for module_id anchors, links, and used-by sections.
- [x] Run verify command.
- [x] Update task state + open PR.

# Progress log
- 2026-01-31 22:08 — Task intake, set T-253 in_progress, created scratchpad, ran task state linter; files: agents/context/tasks_state.yaml, agents/scratchpads/T-253_sphinx_used_by.md; next step: add tests for used-by + links.
- 2026-01-31 22:09 — Commit 86b288c "chore: start T-253 used-by rendering"; next step: add unit tests.
- 2026-01-31 22:16 — Added unit tests for used-by rendering, instance links, and module-id anchors; updated Sphinx document directive expectations; files: tests/unit_tests/docs/test_sphinx_render_used_by.py, tests/unit_tests/docs/test_sphinx_document_directive.py; next step: implement renderer + Sphinx env changes.
- 2026-01-31 22:17 — Commit c92f614 "test: cover used-by rendering and module links"; next step: implement renderer + Sphinx env changes.
- 2026-01-31 22:21 — Implemented depgraph helpers, Sphinx env depgraph build, module-id anchors, instance link rendering, used-by sections, and table cell node support; files: src/asdl/docs/depgraph.py, src/asdl/docs/sphinx_domain.py, src/asdl/docs/sphinx_render.py; next step: run tests.
- 2026-01-31 22:22 — Updated test fixtures to include required top fields after parse error; file: tests/unit_tests/docs/test_sphinx_render_used_by.py; next step: rerun tests.
- 2026-01-31 22:22 — Ran ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render_used_by.py -v (passed); next step: commit implementation and update task status.
- 2026-01-31 22:23 — Commit f2b4f6e "feat: add used-by sections and module links"; next step: open PR.
- 2026-01-31 22:24 — Opened PR https://github.com/Jianxun/ASDL/pull/269; next step: update task state + lint.
- 2026-01-31 22:25 — Set T-253 ready_for_review with PR 269; ran ./venv/bin/python scripts/lint_tasks_state.py; next step: commit scratchpad + task state.

# Patch summary
- Added depgraph helpers for module/instance identifiers and stored dependency graphs in Sphinx env from the project manifest.
- Updated Sphinx doc rendering to use module_id anchors, link instance refs, render used-by sections, and support node cells in tables.
- Added unit coverage for used-by/link rendering and updated document directive expectations.

# PR URL
https://github.com/Jianxun/ASDL/pull/269

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render_used_by.py -v

# Status request (Done / Blocked / In Progress)
Ready for review.

# Blockers / Questions

# Next steps
