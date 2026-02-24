# ADR-0037: CLI Query Semantics v0 (Stage-Aware, Deterministic, Tool-Friendly)

- Status: Accepted
- Date: 2026-02-24

## Context
The project now introduces `asdlc query` for design inspection across authored,
view-resolved, and emitted perspectives. Without an ADR-level semantic contract,
command behavior can drift across subcommands (error handling, ordering, JSON
shape, and terminology), causing flaky automation and review churn.

We need a stable v0 contract that is strict where compatibility matters, while
still allowing limited semantic experimentation in follow-up work.

## Decision
Adopt a unified v0 semantic contract for `asdlc query`.

1. Command and stage model:
   - command group: `asdlc query`
   - v0 subcommands: `tree`, `bindings`, `emit-plan`, `refs`, `instance`,
     `net`, `net-trace`
   - stages: `authored`, `resolved`, `emitted` (default `resolved`)
   - when `--stage emitted` is selected without `--view-config/--view-profile`,
     use baseline view resolution only (no profile rule overrides)

2. JSON contract and terminology:
   - every JSON response includes `schema_version` and `kind`
   - `kind` is the payload discriminator (`query.<subcommand>`)
   - user-facing net connectivity fields use `connections` and `terminal`
     (not internal `endpoint` terminology)

3. Error and match semantics:
   - missing/invalid anchors (`instance`, `net`, `module`) are hard errors
     (diagnostics + exit code `1`)
   - valid queries with no matches return success with empty payload (exit `0`)
   - `refs --module` is exact symbol match only in v0 (no wildcard/decorated
     family expansion)

4. Determinism:
   - fixed input/options must yield deterministic row ordering and stable JSON
     key ordering
   - ordering keys are defined per subcommand in the query spec; v0 keeps
     `instance.connected_nets` lexical and explicitly provisional

## Consequences
- Positive: query outputs become safe for tooling, golden tests, and scripted
  analysis due to stable envelope/error/ordering behavior.
- Positive: user-facing terminology (`connections`, `terminal`) aligns better
  with circuit expectations while preserving internal model freedom.
- Tradeoff: stricter contracts reduce ad-hoc flexibility; some semantics
  (`net-trace` boundaries, path canonicalization) remain intentionally deferred.

## Alternatives
- Keep semantics only in the CLI query spec (no ADR): rejected because core
  behavior could drift during incremental implementation and multi-PR review.
- Defer all semantic freezing until after implementation: rejected because this
  increases rework risk and contract-breaking test churn across command slices.
