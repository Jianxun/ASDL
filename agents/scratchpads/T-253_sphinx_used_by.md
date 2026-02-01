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
- [ ] Add unit tests for instance links, used-by section, and disambiguation.
- [ ] Wire dependency graph into Sphinx env and update renderer for module_id anchors, links, and used-by sections.
- [ ] Run verify command.
- [ ] Update task state + open PR.

# Progress log

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
- 2026-01-31 22:08 — Task intake, set T-253 in_progress, created scratchpad, ran task state linter; files: agents/context/tasks_state.yaml, agents/scratchpads/T-253_sphinx_used_by.md; next step: add tests for used-by + links.
