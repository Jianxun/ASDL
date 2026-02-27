# Project Status

Brief context record for the Architect; reconcile from task status and reviews.

## Current state
- Drafted ADR-0040 (Proposed) and spec updates for backend-owned
  parameterized-subckt system templates:
  `__subckt_header_params__` and `__subckt_call_params__`, with deterministic
  `{params}` rendering as space-delimited `key=value` tokens.
- Drafted ADR-0041 (Proposed) to carry module `parameters` end-to-end through
  AST/PatternedGraph/AtomizedGraph/NetlistIR so header-parameter dispatch is
  contract-reachable instead of emitter-local.
- Drafted ADR-0042 (Proposed) for first-class entry-only
  `global_parameters` and explicit `!{name}` global-reference tokens with
  required-resolution validation and backend-owned declaration/reference syntax.
- Updated specs (`spec_ast`, `spec_netlist_emission`) to define
  `global_parameters` scope, `!{name}` semantics, and emission order (after
  netlist header, before first use).
- Sliced implementation into executor-ready tasks `T-325`..`T-328` with
  dependency chain covering AST/import validation, NetlistIR+emit integration,
  backend-aware token resolution, and backend config/examples regression pass.
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
- `./venv/bin/python scripts/lint_tasks_state.py` (OK with `T-317`..`T-328`)

## Next steps (1-3)
1. Execute `T-325` to land AST/import validation for entry-only
   `global_parameters`.
2. Execute `T-326` and `T-327` to carry globals through NetlistIR and enforce
   backend-aware `!{name}` resolution with fatal unresolved diagnostics.
3. Execute `T-328` to finalize backend config policy and cross-backend
   regression coverage (ngspice/xyce/spectre).

## Risks / unknowns
- Legacy `sim.param` device patterns may overlap with first-class
  `global_parameters`; compatibility/migration policy should be explicit in
  `T-328`.
- Backend reference-style policy for `!{name}` must stay config-owned to avoid
  backend-name branching in emitter code.
- Entry-only scope enforcement depends on robust import-graph context during
  validation; missing context paths must fail deterministically.
