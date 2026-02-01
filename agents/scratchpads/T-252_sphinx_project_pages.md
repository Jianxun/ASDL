# Task summary (DoD + verify)
- Add a project manifest (examples/docs/project.yaml) listing entry ASDL files.
- Implement a Sphinx build hook that generates per-file stub pages under examples/docs/_generated and a toctree that includes them.
- Each stub must render exactly one ASDL file via `asdl:document`.
- Add a small test that verifies deterministic stub ordering.
- Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).

Verify:
- ./venv/bin/sphinx-build -b html examples/docs examples/docs/_build/html

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- [x] Add project manifest and deterministic entry ordering helper.
- [x] Generate stub/toctree pages in Sphinx build hook and wire docs index.
- [x] Add unit test for deterministic stub ordering.
- [x] Run verify (Sphinx build + unit test).
- [x] Update task state + open PR.

# Progress log
- 2026-01-31 21:40 — Task intake, set T-252 in_progress, created scratchpad, ran task state linter; files: agents/context/tasks_state.yaml, agents/scratchpads/T-252_sphinx_project_pages.md; next step: inspect Sphinx docs pipeline.
- 2026-01-31 21:45 — Implemented project manifest parsing, stub/toctree generation helpers, and Sphinx build hook; file: src/asdl/docs/sphinx_domain.py; next step: add unit test.
- 2026-01-31 21:46 — Added deterministic ordering unit test; file: tests/unit_tests/docs/test_sphinx_project_pages.py; next step: commit.
- 2026-01-31 21:47 — Commit 647f32e "Add project manifest parsing and ordering"; next step: wire docs manifest.
- 2026-01-31 21:48 — Wired docs manifest + generated toctree entry; files: examples/docs/index.rst, examples/docs/project.yaml; next step: commit.
- 2026-01-31 21:49 — Commit 830b2d7 "Wire docs project manifest and generated toctree"; next step: run tests.
- 2026-01-31 21:50 — Ran ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_pages.py -v (passed); next step: run sphinx-build.
- 2026-01-31 21:51 — Ran ./venv/bin/sphinx-build -b html examples/docs examples/docs/_build/html (succeeded; warnings about missing _static dir and cached env config value); next step: finalize scratchpad + task state.
- 2026-01-31 21:55 — Opened PR https://github.com/Jianxun/ASDL/pull/268; next step: update task state + lint.
- 2026-01-31 21:55 — Set T-252 ready_for_review with PR 268; ran ./venv/bin/python scripts/lint_tasks_state.py; next step: commit scratchpad + task state.

# Patch summary
- Added project manifest parsing + deterministic ordering helper and generated stub/toctree writer with Sphinx build hook in src/asdl/docs/sphinx_domain.py.
- Added unit test for deterministic manifest ordering in tests/unit_tests/docs/test_sphinx_project_pages.py.
- Added docs manifest and indexed generated toctree in examples/docs/project.yaml and examples/docs/index.rst.

# PR URL
https://github.com/Jianxun/ASDL/pull/268
# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_pages.py -v
- ./venv/bin/sphinx-build -b html examples/docs examples/docs/_build/html (warnings: cached env config value, missing _static)

# Status request (Done / Blocked / In Progress)
Ready for review.

# Blockers / Questions
- None.

# Next steps
- Await review feedback.
- 2026-01-31 21:57 — Review intake: PR targets main, scratchpad + verify logs present; set T-252 to review_in_progress and ran task state linter; next step: inspect diff + scope.
- 2026-01-31 21:59 — Scope review complete against T-252 DoD/links.spec (none present); changes limited to Sphinx domain, examples docs, manifest, and unit test; next step: verify logs and inspect implementation.
- 2026-01-31 21:59 — Verified executor logs for pytest + sphinx-build in scratchpad; no reruns; next step: finalize implementation review.
- 2026-01-31 21:59 — Implementation review complete: manifest parsing + stub/toctree generation align with DoD; no issues found; next step: post PR comment and set review_clean.
- 2026-01-31 22:00 — Posted PR review comment, set T-252 review_clean, and ran task state linter; next step: merge and closeout.
- 2026-01-31 22:00 — Set T-252 status to done (merged true) and ran task state linter; next step: commit review metadata and merge PR.
- 2026-01-31 22:01 — Merged PR 268, deleted remote/local branch, pruned refs, and synced main; task closed.
