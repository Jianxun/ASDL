# Task summary (DoD + verify)
- DoD: Generate a project nav page that orders entries as README, docs, entrances, then libraries. README label uses project_name when set, otherwise the document title. Entrances must render file+module references with descriptions. Update the example Sphinx index to include only the generated project page (no duplicate README entry). Add unit coverage for nav ordering and entrance link rendering.
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_manifest.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect existing Sphinx project manifest/nav rendering.
- Update nav generation + example index + tests.
- Run targeted tests.

# Milestone notes
- Intake complete.

# Patch summary
- Added manifest-aware project nav rendering with README/docs/entrances/libraries ordering, entrance stub coverage, and dependency graph inputs.
- Normalized nav docnames relative to the generated directory and updated example index to avoid README duplication.
- Added tests for nav ordering and entrance link rendering using the v1 manifest fixture.

# PR URL
https://github.com/Jianxun/ASDL/pull/293

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_manifest.py -v

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions

# Next steps
- Await review.
