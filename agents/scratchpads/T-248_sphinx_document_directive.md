# T-248 Implement asdl:document directive (Tier 2)

## Task summary (DoD + verify)
- Implement an `asdl:document` directive that resolves a file path relative to the Sphinx source directory, parses the ASDL file, extracts docstrings, renders docutils nodes using the new renderer, and registers ASDL objects with the domain for cross-references.
- Diagnostics from parsing must surface as Sphinx warnings/errors without crashing.
- Add a small integration test (skip if Sphinx unavailable) that exercises the directive on a sample ASDL file and asserts object registration.
- Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: `./venv/bin/pytest tests/unit_tests/docs/test_sphinx_document_directive.py -v`

## Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

## Plan
- Inspect existing Sphinx domain and renderer integration from T-247.
- Implement the `asdl:document` directive flow: resolve path, parse ASDL, docstring extraction, render nodes, register domain objects, surface diagnostics.
- Add integration test with Sphinx skip guard and verify object registration.
- Run verify command; update scratchpad with results.

## Progress log

## Patch summary

## PR URL

## Verification

## Status request

## Blockers / Questions

## Next steps
## Progress log
- 2026-01-31 00:00 — Task intake complete; read context/contract/task files; created scratchpad; next step: inspect Sphinx domain/renderer code.
- 2026-01-31 00:00 — Set T-248 status to in_progress and linted tasks_state; created feature branch; next step: implement directive.
- 2026-01-31 10:20 — Implemented asdl:document directive, diagnostics reporting, and object registration; updated sphinx_domain helpers; next step: add integration test.
- 2026-01-31 10:30 — Added Sphinx integration test for asdl:document registration; next step: run pytest.
- 2026-01-31 10:35 — Ran `./venv/bin/pytest tests/unit_tests/docs/test_sphinx_document_directive.py -v` (pass); next step: commit changes.
- 2026-01-31 10:40 — Commit 74833d0: add asdl:document directive, diagnostics reporting, and integration test; files: src/asdl/docs/sphinx_domain.py, tests/unit_tests/docs/test_sphinx_document_directive.py, agents/scratchpads/T-248_sphinx_document_directive.md, agents/context/tasks_state.yaml; next step: finalize status/PR.
- 2026-01-31 10:50 — Opened PR https://github.com/Jianxun/ASDL/pull/263; next step: update task status + lint.

## Patch summary
- Implemented `asdl:document` directive to parse ASDL sources, log diagnostics, register domain objects, and render docutils sections with implicit targets for TOC stability.
- Added a Sphinx integration test that builds a tiny project and asserts ASDL object registration.

## PR URL
- https://github.com/Jianxun/ASDL/pull/263

## Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_document_directive.py -v

## Status request
- ready_for_review

## Blockers / Questions
- None.

## Next steps
- Await review.
- 2026-01-31 11:00 — Updated T-248 status to ready_for_review (PR 263) and ran lint_tasks_state.py; next step: commit metadata updates.
- 2026-01-31 11:05 — Commit f46bf07: update T-248 status to ready_for_review and record PR metadata; files: agents/context/tasks_state.yaml, agents/scratchpads/T-248_sphinx_document_directive.md; next step: push branch.
