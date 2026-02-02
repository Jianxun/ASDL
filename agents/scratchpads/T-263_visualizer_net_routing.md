# Task summary (DoD + verify)
- DoD: Build topology-aware edge generation in the webview: star connects endpoint pins to hubs; mst builds a deterministic Manhattan MST between endpoints plus the hub as an MST node; trunk builds a hub-oriented rectilinear trunk with junction nodes and branch drops (horizontal default when no hub placement). Use schematic_hints.net_groups (when present in the payload) to split endpoints per hub group and map to hub order. Ensure pin labels use net IDs/labels instead of hub IDs so mst/trunk still label correctly, and keep connect_by_label suppression behavior. Update dev harness and dev payload fixtures to exercise mst/trunk.
- Verify: npm --prefix extensions/asdl-visualizer run build:webview

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Inspect current webview edge generation, payload types, dev harness/payload.
- Implement star/mst/trunk routing with net group splitting and labeling adjustments.
- Update dev harness/payloads to exercise mst/trunk.
- Run webview build verify.
- Todo:
  - [ ] Implement topology-aware routing + junction nodes in webview.
  - [ ] Update dev harness and dev payload fixtures for mst/trunk coverage.
  - [ ] Run build:webview and record results.

# Progress log

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
