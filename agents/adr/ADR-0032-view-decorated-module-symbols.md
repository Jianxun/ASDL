# ADR-0032: View-Decorated Module Symbols Use `cell@view` With Multi-View Emission Names

- Status: Accepted
- Date: 2026-02-22

## Context
ASDL needs multiple implementation variants for the same logical cell (for
example schematic, behavioral, and extracted variants) while keeping simulator
output stable and tool-friendly. File-name heuristics (such as
`*.schematic.asdl`) are too rigid and do not scale to multiple experimental
schematics or multiple behavioral fidelity levels.

We need:
- an explicit authoring syntax for module variants
- a stable logical cell identity independent of file naming
- netlist emission that supports mixed subtree substitutions in one netlist

The binding configuration schema and precedence are intentionally deferred to a
follow-up decision.

## Decision
Adopt view-decorated module symbols:

1. Module declaration names may be either:
   - `cell`
   - `cell@view`
2. `cell` and `view` each use identifier grammar
   `[A-Za-z_][A-Za-z0-9_]*`.
3. Exactly zero or one `@` is allowed in a module symbol.
4. Logical identity is `cell`; `view` is a selectable implementation token.
5. Netlist emission is realization-based:
   - emit one subckt/module per resolved `(cell, view)` used in the design
   - default/undecorated realization emits as `cell`
   - non-default realizations emit as `cell_<view>` (deterministic, sanitized)
   - instance calls reference the resolved realization name
6. Binding-config schema (profiles/rules/precedence) is deferred; this ADR
   defines only naming, identity, and emission-surface rules.

## Consequences
- Positive: supports many variants (`@behav`, `@cascode`, `@behav_lite`) without
  naming heuristics tied to file paths.
- Positive: supports mixed-view substitution inside one emitted netlist (for
  example one instance uses default while another uses `behav`).
- Positive: simulator-facing names avoid `@` by using deterministic underscore
  suffixed realization names.
- Tradeoff: parser/symbol validation and module identity handling must support
  decorated symbols and detect malformed forms.

## Alternatives
- File-name-based view inference (e.g., `foo.behav.asdl`): rejected because it
  is brittle and does not represent semantic identity in-language.
- Separate module names (e.g., `foo_behav`): rejected because it loses explicit
  `cell` vs `view` semantics and complicates future binding selection.
