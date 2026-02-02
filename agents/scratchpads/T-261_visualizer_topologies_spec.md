# Task summary (DoD + verify)
- DoD: Update docs/specs/spec_asdl_visualizer.md to define per-net topology selection (star | mst | trunk), including the updated .sch.yaml schema shape for net_hubs entries, defaults, and legacy map compatibility. Specify how schematic_hints.net_groups map to hub groups and how topology applies per group. Describe MST routing using Manhattan endpoint distances with deterministic tie-breakers and include the hub as an MST node. Specify trunk routing that follows hub orientation (horizontal for R0/MX, vertical for R90/MXR90; default horizontal when hub placement is missing) and branches to endpoints.
- Verify: none

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Review current visualizer spec sections for schematic sidecar + routing rules.
- Update schema docs for net_hubs topology selection, defaults, and legacy map handling.
- Specify net_groups-to-hub-group mapping plus MST/trunk routing rules.
- Record progress, summarize patch, and verify (no tests required).

# Progress log
- 2026-02-01 20:22 — Task intake and scope confirmation; reviewed executor role + task docs; next step update visualizer spec.
- 2026-02-01 20:23 — Updated visualizer spec with net_hubs topology schema, hub group mapping, and routing topology rules; files touched: docs/specs/spec_asdl_visualizer.md; next step commit changes.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
