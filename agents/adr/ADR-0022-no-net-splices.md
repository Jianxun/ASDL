# ADR-0022: Forbid Spliced Net Names (LHS)

Status: Accepted

## Context
Pattern splicing (`;`) is useful for flattening expansions, but using splices in
net names (the LHS of `nets:` bindings) obscures net identity, complicates
diagnostics, and makes future visualization and port-ordering less explicit.
The refactor pipeline aims to keep net entries as stable, first-class rows.

## Decision
Disallow splices in net name expressions (LHS of `nets:`). Net entries must be
split per pattern segment, e.g. use multiple `nets` entries instead of a single
spliced key. Splicing remains supported in other expression positions unless
explicitly restricted elsewhere.

## Consequences
- Net names containing `;` are treated as errors in the refactor pipeline.
- Authors must split net entries to express multiple segments.
- Visualization, diagnostics, and port-order semantics remain one-net-per-row.

## Alternatives
- Allow spliced net names and flatten segments during binding; rejected due to
  ambiguous net identity and harder visualization.
- Allow splices temporarily with a warning; rejected to avoid entrenching the
  pattern in new content.
