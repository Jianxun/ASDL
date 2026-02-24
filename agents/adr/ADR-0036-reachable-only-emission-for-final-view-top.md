# ADR-0036: Reachable-Only Emission from Final Resolved Top (Keep Default Name as `cell`)

- Status: Accepted
- Date: 2026-02-24

## Context
View-binding resolution can apply path-scoped overrides that create mixed-view
realizations of a module. The previous behavior preserved original authored
module blocks and added realized variants, which can emit both reachable and
unreachable subckts in one output. This is confusing for users reading generated
netlists because unused modules still appear.

At the same time, naming should remain concise for canonical/default modules.
Using `cell_default` everywhere is more explicit but adds noise for common
cases.

## Decision
Adopt reachable-only netlist emission rooted at the final resolved top, while
keeping default naming compact.

1. Emission root:
   - resolve the final top realization after applying selected view profile
   - start emission traversal from that resolved top

2. Reachability:
   - emit only modules reachable via transitive instance references from the
     resolved top
   - do not emit unreachable authored definitions

3. Naming policy:
   - default/undecorated and `cell@default` emit as `cell`
   - non-default decorated symbols emit as `cell_<view>`

4. Collision policy:
   - retain deterministic global collision handling with ordinal suffixes
     (`__2`, `__3`, ...)
   - keep compile-log name-map and warning observability

## Consequences
- Positive: emitted netlists are easier to read because only active topology is
  present.
- Positive: default naming remains concise and familiar (`cell`).
- Tradeoff: breaking change for workflows that depended on extra unreachable
  module blocks being present in output.

## Alternatives
- Keep previous behavior (emit original + realized variants): rejected due to
  user confusion and unnecessary output noise.
- Always emit explicit default names (`cell_default`): rejected to preserve
  canonical readability for the common default case.
