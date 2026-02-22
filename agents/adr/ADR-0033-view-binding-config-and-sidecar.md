# ADR-0033: View Binding Config Uses `view_order` + Ordered Rules with Resolved Sidecar Output

- Status: Accepted
- Date: 2026-02-22

## Context
ASDL now supports view-decorated module symbols (`cell@view`) and mixed-view
emission realizations (`cell` and `cell_<view>`). We need a deterministic
configuration system to resolve instance bindings across a hierarchy while
keeping the outcome explicit and inspectable.

Key requirements:
- global baseline precedence across views
- local overrides by explicit rules
- lightweight authoring (optional rule IDs)
- inspectable compile output for resolved bindings

## Decision
Adopt a view-binding config system with:

1. Profiles:
   - top-level config map of named profiles
   - each profile defines `view_order` and optional `rules`

2. Global baseline:
   - `view_order` defines baseline precedence per logical cell
   - baseline resolution happens before rule overrides

3. Ordered overrides:
   - `rules` are evaluated in file order
   - later matching rules override earlier matching rules
   - rule `id` is optional; compiler assigns deterministic default `rule<k>`
     by 1-based list position

4. Match model:
   - `match` is a typed object (`path`, `inst`, `module`)
   - missing `path` means root scope (top-level instances)
   - rules may target by instance name, module logical name, and/or scoped path

5. Sidecar output:
   - compiler emits an inspectable sidecar list of resolved bindings
   - each entry includes at least `path`, `instance`, and `resolved`
   - `resolved` is full module symbol (`cell` or `cell@view`)

## Consequences
- Positive: deterministic and compact authoring model with explicit override
  semantics.
- Positive: sidecar output makes final binding outcomes transparent for debug
  and CI checks.
- Tradeoff: path-scoping semantics must be documented precisely to avoid
  surprises in large hierarchies.

## Alternatives
- Heuristic string selectors (for example `<module>` magic keys): rejected due
  to parser ambiguity and poor extensibility.
- Embedding rule provenance into core IR objects: rejected to keep core IR
  policy-light; sidecar carries inspectable binding outcomes.
