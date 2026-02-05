# Task summary (DoD + verify)
- DoD: Update the Sphinx ASDL domain to parse the v1 project manifest schema (schema_version, project_name, readme, docs, entrances, libraries) while preserving YAML list order. Library entries must expand all .asdl files under each library root, honoring exclude globs relative to the library root (no implicit filtering). Remove legacy manifest entry sorting/expansion from the project flow. Add unit coverage for parsing and exclude handling.
- Verify: ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_manifest.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect current manifest parsing + library expansion in Sphinx domain and tests.
- Add/adjust parsing for v1 schema and ordered lists; update library expansion/exclude handling.
- Update tests/fixtures for v1 manifest parsing + excludes; run targeted pytest.

# Todo
- [x] Update manifest parsing/expansion to v1 schema without legacy sorting.
- [x] Add fixtures + tests for manifest parsing and exclude handling.
- [x] Run targeted pytest verify command.

# Milestone notes
- Intake complete.
- Implemented manifest v1 parsing + library expansion; added fixtures/tests.

# Patch summary
- Added v1 project manifest parsing with ordered lists and library expansion.
- Added manifest fixtures + tests for parsing order and exclude globs; updated project page tests.

# PR URL
- TBD

# Verification
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_manifest.py -v
- ./venv/bin/pytest tests/unit_tests/docs/test_sphinx_project_pages.py -v

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions

# Next steps
