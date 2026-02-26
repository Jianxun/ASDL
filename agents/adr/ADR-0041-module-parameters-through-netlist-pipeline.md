# ADR-0041: Carry Module Parameters Through the Netlist Pipeline

**Status**: Proposed  
**Date**: 2026-02-26

## Context

ADR-0040 introduced parameterized subckt system templates
(`__subckt_header_params__`, `__subckt_call_params__`). Module-instance
parameterized calls are already representable, but module-header parameterized
emission is not reliably reachable unless module default parameters are carried
end-to-end through the core pipeline.

Today, module parameters are not a stable first-class field across all
pipeline layers, which makes header dispatch behavior fragile and
implementation-specific.

## Decision

Introduce and standardize module-level `parameters` as a first-class field
across the main pipeline:

- AST `ModuleDecl.parameters`
- PatternedGraph module bundle `parameters`
- AtomizedModuleGraph `parameters`
- NetlistIR `NetlistModule.parameters`

Rules:

- Canonical field name is `parameters` (not `params`) for module definitions.
- NetlistIR stores string-valued parameter defaults in deterministic key order.
- Emitter selects:
  - `__subckt_header_params__` when `NetlistModule.parameters` is non-empty
  - `__subckt_header__` otherwise
- `{params}` rendering remains deterministic space-delimited `key=value`
  tokens.

## Consequences

- Parameterized subckt header rendering becomes explicit and reachable by
  contract, not by ad-hoc fields.
- Pipeline contracts become more consistent (`parameters` naming symmetry
  across modules/devices/instances).
- Requires coordinated updates to models, lowerers, dumps, and regression
  fixtures across multiple subsystems.

## Alternatives

- Keep module-header parameter handling as emitter-local ad-hoc data.
  - Rejected: brittle and not traceable through IR contracts.
- Restrict parameterized templates to calls only (no header params support).
  - Rejected: fails legitimate simulator flows that require parameterized
    subckt definitions.
