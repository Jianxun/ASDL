# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- View-decorated symbol and view-binding specs were tightened and aligned with
  accepted ADRs: ADR-0034 (DFS-stable ordinal collision naming) and ADR-0035
  (consolidated compile log).
- ADR-0036 is now accepted: netlist emission is rooted at the final resolved
  top realization and emits reachable modules only; default naming remains
  `cell` and non-default stays `cell_<view>`.
- `cell@default` normalization is accepted and documented; rules explicitly
  override authored decorated refs in binding resolution.
- Collision naming policy is now `base`, `base__2`, `base__3`, ... in emission
  traversal order, including decorated-vs-literal base clashes.
- Full-path provenance via `{file_id}` in subckt headers remains the preferred
  end-to-end behavior; partial pipeline invocation must provide metadata.
- Completed tasks `T-299`..`T-302` are archived.
- New active task wave is `T-303`..`T-304` for reachable-only emission cutover.

## Last verified status
- `./venv/bin/python scripts/lint_tasks_state.py` (run after archiving/slicing `T-299`..`T-302` and reslicing reachable-only cutover tasks)

## Next steps (1-3)
1. T-303: emit only modules reachable from final resolved top realization.
2. T-304: preserve canonical realized naming (`cell`/`cell_<view>`) with deterministic collision suffixing under reachable-only emission.
3. Ensure each implementation task lands with its own regression updates (no standalone regression follow-up task).

## Risks / unknowns
- Reachability pruning is a behavioral break for any flow relying on emitted
  but unreachable authored modules.
- Collision suffix numbering can shift when previously unreachable colliders are
  removed from traversal; regression updates must assert only the new policy.
- Compile-log expectations (`emission_name_map`, warning counts) need careful
  fixture updates to avoid flaky diffs during cutover.
