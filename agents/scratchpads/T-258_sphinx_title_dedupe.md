# Task summary (DoD + verify)
- DoD: Always use the ASDL file stem as the page title (do not promote `document.top` or single-module names). Render `top` as a separate document-level "Top module" section placed after Overview and before Imports so it is visible without duplicating module titles. Update unit coverage to assert title selection and top-section rendering. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect current title/overview/import rendering in sphinx_render.
- Update title selection to always use file stem and insert "Top module" section.
- Update tests to assert title selection and top section placement.
- Run verify command.

# Progress log
- 2026-02-01 00:00 — Task intake; updated scratchpad DoD/plan to match T-258; next step set task in_progress and branch.
- 2026-02-01 00:01 — Updated Sphinx render tests for file-stem titles and Top module section expectations; files touched: tests/unit_tests/docs/test_sphinx_render.py; next step commit tests then update renderer.
- 2026-02-01 00:02 — Committed task prep scratchpad/status updates (2c4968f); files touched: agents/context/tasks_state.yaml, agents/scratchpads/T-258_sphinx_title_dedupe.md; next step commit tests.
- 2026-02-01 00:03 — Committed title/top module test coverage (7644be1); files touched: tests/unit_tests/docs/test_sphinx_render.py, agents/scratchpads/T-258_sphinx_title_dedupe.md; next step update renderer logic.
- 2026-02-01 00:04 — Implemented file-stem titles and Top module section rendering; files touched: src/asdl/docs/sphinx_render.py, src/asdl/docs/sphinx_domain.py; next step commit renderer changes.
- 2026-02-01 00:05 — Committed renderer updates for file-stem titles and Top module section (395b758); files touched: src/asdl/docs/sphinx_render.py, src/asdl/docs/sphinx_domain.py, agents/scratchpads/T-258_sphinx_title_dedupe.md; next step run tests.
- 2026-02-01 00:06 — Verified pytest tests/unit_tests/docs/test_sphinx_render.py -v (passed); next step update scratchpad summary and prep PR.
- 2026-02-01 00:07 — Committed scratchpad log updates (3febfc5); files touched: agents/scratchpads/T-258_sphinx_title_dedupe.md; next step open PR.
- 2026-02-01 00:08 — Opened PR https://github.com/Jianxun/ASDL/pull/277; next step set task ready_for_review.
- 2026-02-01 00:09 — Set T-258 ready_for_review in tasks_state.yaml and linted tasks_state; next step finalize scratchpad summary.

# Patch summary
- Use file-stem document titles in Sphinx render/domain and add a "Top module" section before imports.
- Add helpers to render/link the top module entry when present.
- Extend Sphinx render tests for title selection and top module ordering/content.

# PR URL
- https://github.com/Jianxun/ASDL/pull/277

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_render.py -v

# Status request
- Ready for review.

# Blockers / Questions
- None.

# Next steps
- Await reviewer feedback.
