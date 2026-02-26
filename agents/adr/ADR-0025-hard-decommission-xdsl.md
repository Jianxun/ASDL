# ADR-0025: Hard Decommission xDSL Pipeline

Status: Accepted

## Context
The refactor pipeline now emits netlists end-to-end via PatternedGraph ->
AtomizedGraph -> NetlistIR -> netlist emitter. The legacy xDSL GraphIR/IFIR
pipeline and associated CLI `ir-dump` tooling are no longer required for the
active path but continue to impose maintenance costs, dependency coupling, and
documentation ambiguity.

## Decision
Hard decommission the xDSL pipeline and artifacts from the active tree:
- Remove CLI `ir-dump` and any xDSL pipeline entrypoints from the CLI surface.
- Remove xDSL IR code/tests from the active repository tree.
- Move legacy GraphIR/IFIR/NFIR and xDSL-era pipeline specs from `docs/specs/`
  into `docs/legacy/` with a decommission notice.
- Remove the `xdsl` dependency from default installs (no legacy extras).

## Consequences
- Active code no longer depends on xDSL; default installs are lighter and
  simpler.
- Legacy xDSL behavior is documented in `docs/legacy/` and git history for
  reference.
- Users relying on `ir-dump` or GraphIR/IFIR must migrate to NetlistIR or the
  refactor inspection tools.

## Alternatives
- Keep xDSL behind a legacy optional extra: rejected to avoid split support
  paths and ongoing maintenance costs.
- Leave xDSL artifacts in place but unused: rejected due to continued dependency
  and documentation drag.
