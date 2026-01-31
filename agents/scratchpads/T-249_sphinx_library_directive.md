# Task summary (DoD + verify)
- DoD: Add a directory-capable directive or helper (e.g., `asdl:library`) that expands all `.asdl` files under a given directory and renders them in deterministic order. Update examples/docs to use the directive for `examples/libs` so Tier 2 docs build without pre-generated Markdown. Provide a small test for directory expansion ordering. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/sphinx-build -b html examples/docs examples/docs/_build/html

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect existing Sphinx domain/directive implementation and current docs wiring.
- Implement directory-capable directive/helper and deterministic ordering.
- Add unit test for directory expansion ordering.
- Update examples/docs to use new directive for examples/libs.
- Run verify command.

# Progress log
- 2026-01-31 03:06 — Task intake; reviewed role instructions and task metadata; next step inspect Sphinx domain/docs.
- 2026-01-31 03:06 — Initialized scratchpad, set T-249 in_progress, ran tasks_state lint, created feature branch `feature/T-249-sphinx-library-directive`; next step implement helper + tests.
- 2026-01-31 03:07 — Added deterministic ASDL library file collection helper + ordering test; files: src/asdl/docs/sphinx_domain.py, tests/unit_tests/docs/test_sphinx_library_directive.py; commit 5705897; next step add library directive wiring.
- 2026-01-31 03:08 — Implemented reusable ASDL document renderer and added asdl:library directive wiring; file: src/asdl/docs/sphinx_domain.py; commit 4a0fc87; next step update examples/docs to use directive.
- 2026-01-31 03:09 — Updated examples/docs index and README to use asdl:library directive; files: examples/docs/index.rst, examples/docs/README.md; commit 84c3b11; next step run tests/verification.
- 2026-01-31 03:10 — Ran pytest tests/unit_tests/docs/test_sphinx_library_directive.py -v; result: PASS; next step run Sphinx build verify.
- 2026-01-31 03:14 — Adjusted library file collection defaults (skip _archive, prefer *_doc) and excluded examples/docs/libs markdown from Sphinx sources; files: src/asdl/docs/sphinx_domain.py, examples/docs/conf.py; next step rerun Sphinx build.
- 2026-01-31 03:14 — Ran ./venv/bin/sphinx-build -b html examples/docs examples/docs/_build/html; result: SUCCESS with 1 warning (missing _static dir).
- 2026-01-31 03:14 — Refined library file selection defaults and docs exclude_patterns; files: src/asdl/docs/sphinx_domain.py, examples/docs/conf.py; commit be64505; next step finalize status and PR.
- 2026-01-31 03:16 — Opened PR https://github.com/Jianxun/ASDL/pull/264; next step set task status ready_for_review.
- 2026-01-31 03:16 — Set T-249 status to ready_for_review (PR 264) and ran tasks_state linter; next step await review.

# Patch summary
- Added deterministic ASDL library file collection with archive/doc preferences and new `asdl:library` directive rendering.
- Added ordering unit test for library file expansion.
- Updated examples/docs index/README and Sphinx exclude patterns to render libraries via directive without pre-generated Markdown.

# PR URL
https://github.com/Jianxun/ASDL/pull/264

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_library_directive.py -v (PASS)
- ./venv/bin/sphinx-build -b html examples/docs examples/docs/_build/html (SUCCESS; warning: missing `_static` dir)

# Status request (Done / Blocked / In Progress)
Ready for review.

# Blockers / Questions
- None.

# Next steps
- Await review feedback.
