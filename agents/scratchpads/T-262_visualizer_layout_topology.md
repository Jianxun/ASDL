# Task summary (DoD + verify)
- DoD: Update visualizer layout payload types and read/merge logic to support per-net topology selection with backward-compatible parsing of legacy net_hubs maps. Default missing topology to star and preserve hub placement data for all groups. Extend VisualizerDump/GraphPayload types to carry schematic_hints.net_groups/hub_group_index so the webview can map endpoints to hub groups. Update dev payload generation to emit the new net_hubs shape for sample layouts.
- Verify: npm --prefix extensions/asdl-visualizer run build:extension

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect visualizer extension types/layout merge logic and dev payload generation.
- TODO: Update extension types + graph builder to include schematic_hints net_groups/hub_group_index.
- TODO: Normalize net_hubs parsing/merge with default topology and legacy map support.
- TODO: Update dev payload generation to emit new net_hubs shape + schematic_hints passthrough.
- Run verify command.

# Progress log

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
- 2026-02-01 20:32 — Task intake: reviewed role, tasks, contract, status; created scratchpad; set T-262 in_progress; next step inspect visualizer extension types/layout.
- 2026-02-01 20:39 — Updated extension layout/types for topology + schematic hints; adjusted net_hubs merge normalization and defaults; next step update dev payload generator.
- 2026-02-01 20:39 — Updated build-dev-payload graph + layout merge to emit new net_hubs shape and schematic_hints passthrough; next step review diff and commit.
- 2026-02-01 20:40 — Commit f92b852 (start T-262 layout schema support); files: agents/context/tasks_state.yaml, agents/scratchpads/T-262_visualizer_layout_topology.md, extensions/asdl-visualizer/src/extension/{types.ts,layout.ts,symbols.ts}; next step update dev payload generator.
