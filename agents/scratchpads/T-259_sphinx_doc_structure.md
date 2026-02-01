# Task summary (DoD + verify)
- DoD: Render document titles as the ASDL file name with extension (e.g., `inv.asdl`) and treat Imports as a file-level section. Ensure the file Overview uses only file-level docstrings. Module-level overviews must be labeled "Notes" (not "Overview") to avoid confusion with file-level Overview. Update unit coverage to assert title selection and section ordering. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect document title + section rendering in sphinx_render.
- Implement file-name titles and rename module overview to "Notes".
- Ensure file-level Overview/Imports remain separate from module sections.
- Update tests to assert title selection and section ordering.
- Run verify command.

# Progress log
- 2026-02-01 11:38 — Task intake: align Sphinx doc titles/sections with file/module semantics; will adjust renderer and tests; next step inspect sphinx_render.
- 2026-02-01 11:39 — Updated Sphinx render tests for file-title with extension, no file Overview fallback, Notes ordering, and Imports ordering; files: tests/unit_tests/docs/test_sphinx_render.py; next step adjust renderer.
- 2026-02-01 11:40 — Commit a704825 test updates for title/section ordering; files: tests/unit_tests/docs/test_sphinx_render.py, agents/scratchpads/T-259_sphinx_doc_structure.md; next step implement renderer changes.
- 2026-02-01 11:40 — Updated renderer to use file name titles and limit Overview to file docstrings; files: src/asdl/docs/sphinx_render.py; next step run tests.
- 2026-02-01 11:40 — Commit 2fbcc96 renderer updates for file-name titles and file-only Overview; files: src/asdl/docs/sphinx_render.py, agents/scratchpads/T-259_sphinx_doc_structure.md; next step run verify tests.
- 2026-02-01 11:41 — Verified pytest docs render tests: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v (pass).
- 2026-02-01 11:42 — Opened PR https://github.com/Jianxun/ASDL/pull/278; next step set task ready_for_review.
- 2026-02-01 11:42 — Set T-259 ready_for_review in tasks_state.yaml and linted tasks_state; next step finalize scratchpad summary.
- 2026-02-01 11:44 — Review intake: confirmed PR targets main and is mergeable; next step set review_in_progress and verify checks/logs.
- 2026-02-01 11:44 — Set T-259 to review_in_progress; next step validate scope and diffs.
- 2026-02-01 11:46 — Verified executor test log present for ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v; no additional checks run; next step scope and code review.
- 2026-02-01 11:46 — Scope review complete: changes limited to sphinx_render + tests + task metadata, aligned with DoD; next step record review decision.
- 2026-02-01 11:46 — Posted review comment and marked review_clean; next step merge and closeout.

# Patch summary
- Updated Sphinx doc titles to use file names with extensions and restricted Overview to file docstrings only.
- Adjusted render tests to assert file-name titles, Notes usage, and Imports/module ordering.

# PR URL
- https://github.com/Jianxun/ASDL/pull/278

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v

# Status request
- Ready for review.

# Blockers / Questions
- None.

# Next steps
- Await reviewer feedback.
