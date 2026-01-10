Title: ADR-0010: Patterned Instance Parameter Expansion
Status: Accepted

## Context
Instance parameters are currently preserved as raw strings. Authors want to use
pattern tokens in parameter values (e.g., `m=<1|2|4>`) to avoid repetitive
per-instance overrides.

## Decision
Allow pattern tokens in instance parameter values and expand them during
elaboration after instance-name expansion.

Rules:
- Expand instance names to `N` atoms first.
- For each parameter value:
  - If expansion length is **1**, broadcast to all `N` instances.
  - If expansion length is **N**, zip by instance index.
  - Otherwise emit an error (no cross-product).
- Named patterns (`<@name>`) are allowed in parameter values.
- Expansion uses explicit concatenation (ADR-0009).

## Consequences
- Parameter values may vary per instance without duplicating instance entries.
- Adds param-length diagnostics and a new elaboration step for params.

## Alternatives
- Cross-product expansion across multiple params. Rejected: combinatorial
  explosion and unclear intent.
