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
- Executor batch `T-303` and `T-304` is complete and merged (PRs 326, 327),
  and latest PR changes are pulled locally.
- Query subsystem scope is now drafted in `docs/specs/spec_cli_query.md`
  (`asdlc query` with stage-aware inspection subcommands).

## Last verified status
- `./venv/bin/python scripts/lint_tasks_state.py` (OK with `T-303`/`T-304` marked done)

## Next steps (1-3)
1. Slice the next wave for `asdlc query` implementation against `docs/specs/spec_cli_query.md` (tree/bindings/emit-plan/refs/instance/net/net-trace).
2. Resolve v0.x open decisions captured in the query spec (path canonicalization, emitted-stage defaults, `net-trace` equivalence boundaries, diagnostics policy).
3. Ship an initial query MVP with deterministic JSON output contracts and regression tests.

## Risks / unknowns
- Query output contract may churn if open decisions are implemented ad hoc
  without freezing schema/version semantics first.
- Path canonicalization for patterned instance names can create hidden mismatch
  between authored references and query selectors if not defined early.
- `net-trace` hierarchy equivalence semantics need clear boundaries to avoid
  ambiguous downstream plotting/postprocessing behavior.
