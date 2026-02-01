# Task summary (DoD + verify)
- DoD: Implement a dependency-graph builder that uses the import resolver to produce module/instance edges from one or more entry ASDL files. Define a stable JSON schema (files, modules, instances, edges, unresolved) and provide serialization helpers. Module identifiers must be `name__hash8` where `hash8 = sha1(file_id)[:8]`; use `module_id` for tooling/anchors while keeping `name` for display. Include focused unit coverage for graph construction and edge resolution using a small fixture. Do not touch unrelated style docs (e.g., docs/code_styles/docstrings_comments.md).
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_depgraph.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect existing depgraph/documentation utilities and import resolver APIs.
- Define dependency graph model + JSON schema and implement builder.
- Add unit tests for graph construction, edge resolution, and JSON serialization.
- Run verify command.

# Progress log
- 2026-01-31 21:10 — Task intake; reviewed role instructions and task metadata; next step inspect depgraph/import resolver code.
- 2026-01-31 21:10 — Initialized scratchpad, set T-250 in_progress, ran tasks_state lint, created feature branch `feature/T-250-depgraph-model`; next step review depgraph implementation surface.
- 2026-01-31 21:10 — Task understanding: add depgraph model/JSON helpers + builder leveraging import resolver to map module/instance edges with module_id hashing; add focused unit tests; keep changes scoped.
- 2026-01-31 21:19 — Implemented dependency graph model, builder, and JSON serialization helpers; added exports in docs package; files: src/asdl/docs/depgraph.py, src/asdl/docs/__init__.py; next step add unit tests.
- 2026-01-31 21:19 — Added depgraph unit test fixture covering edge resolution and unresolved cases; file: tests/unit_tests/docs/test_depgraph.py; next step run verify.
- 2026-01-31 21:19 — Ran ./venv/bin/pytest tests/unit_tests/docs/test_depgraph.py -v; result: PASS; next step commit changes.
- 2026-01-31 21:19 — Committed depgraph model + tests (c83c522); next step update scratchpad summary and proceed to closeout.
- 2026-01-31 21:20 — Opened PR https://github.com/Jianxun/ASDL/pull/266; next step set task status ready_for_review.
- 2026-01-31 21:20 — Set T-250 status to ready_for_review (PR 266) and ran tasks_state linter; next step finalize scratchpad closeout.

# Patch summary
- Added dependency graph model, builder, and JSON serialization helpers with module_id hashing and unresolved tracking.
- Exposed depgraph utilities in the docs package API.
- Added unit test fixture covering edge resolution and unresolved cases.

# PR URL
https://github.com/Jianxun/ASDL/pull/266

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_depgraph.py -v (PASS)

# Status request (Done / Blocked / In Progress)
Ready for review.

# Blockers / Questions
- None.

# Next steps
- Await review feedback.
