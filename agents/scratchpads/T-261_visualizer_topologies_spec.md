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
- 2026-02-01 20:24 — Committed spec updates; commit 223cbb1; next step verification/polish scratchpad.
- 2026-02-01 20:24 — Recorded patch summary and verification skip note (docs-only); next step update task state/PR.
- 2026-02-01 20:25 — Opened PR https://github.com/Jianxun/ASDL/pull/280 after pushing branch; next step update task state and scratchpad.
- 2026-02-01 20:25 — Set T-261 status to ready_for_review with PR 280 and ran lint_tasks_state.py; files touched: agents/context/tasks_state.yaml; next step final commit/push.
- 2026-02-01 20:27 — Review intake: confirmed PR targets main, task ID present, scratchpad + verification note included; next step set review_in_progress and inspect spec changes.
- 2026-02-01 20:28 — Verified checks: no required verify commands; docs-only skip recorded; next step scope review.
- 2026-02-01 20:28 — Scope review complete; spec updates align DoD for net_hubs schema, net_groups mapping, and MST/trunk routing; next step decide review outcome.
- 2026-02-01 20:29 — Posted PR review comment with review-clean decision and non-blocking trunk note; next step set review_clean status.
- 2026-02-01 20:29 — Set T-261 status to review_clean; next step closeout (set done, merge, cleanup).

# Patch summary
- Documented net_hubs topology schema with defaults/legacy shape and hub group ordering rules.
- Added per-group routing topology definitions for star/mst/trunk (including Manhattan MST + deterministic tie-breaker and trunk orientation rules).

# PR URL
- https://github.com/Jianxun/ASDL/pull/280

# Verification
- Not run (docs-only changes; no verify command listed).

# Status request (Done / Blocked / In Progress)
- Ready for review

# Blockers / Questions

# Next steps
- Update tasks_state to ready_for_review with PR number.
