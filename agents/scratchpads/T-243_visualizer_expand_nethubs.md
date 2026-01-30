# Task summary (DoD + verify)
- DoD: Expand literal-enum net names in visualizer dumps so net hubs mirror instance/endpoint literal expansions. Emit expanded net IDs and remap endpoint net_id to the corresponding expansion index (default index 0) when present, falling back with diagnostics if counts diverge. Ensure expanded nets carry updated endpoint_ids. Add CLI unit coverage for expanded nets and endpoint remapping in visualizer dumps.
- Verify: ./venv/bin/pytest tests/unit_tests/cli/test_visualizer_dump.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect visualizer dump implementation and existing expansion logic.
- Update net hub expansion/remap behavior with diagnostics.
- Add/adjust CLI unit tests for expanded nets and remapped endpoints.
- Run targeted tests.

# Progress log
- 2026-01-30 00:00 — Initialized scratchpad for T-243; next step update task state and branch.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
- 2026-01-30 00:07 — Set T-243 status to in_progress, ran lint, created feature branch; next step inspect visualizer dump/net expansion behavior.
- 2026-01-30 00:18 — Added CLI unit test coverage for net expansion + endpoint remap in visualizer dump; files: tests/unit_tests/cli/test_visualizer_dump.py; next step implement net expansion/remap logic in dump.
