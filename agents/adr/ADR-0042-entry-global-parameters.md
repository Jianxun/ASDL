# ADR-0042: Entry-Scoped Global Parameters and Explicit Global References

**Status**: Proposed  
**Date**: 2026-02-27

## Context

Simulation decks often require file-level global parameters (for example testbench
bias values) that are referenced in device statements and analysis directives.
Current ASDL authoring can model parameter directives as ordinary devices (for
example `sim.param`), but this is semantically indirect and leads to fragile
token workarounds when backend reference syntax differs (`{v}` vs `v`).

We need a first-class, backend-agnostic model for global parameters while
keeping module/subckt parameter semantics unchanged and deterministic.

## Decision

Introduce entry-file-only first-class global parameters and explicit global
reference tokens:

- Add top-level `global_parameters: Dict[str, ParamValue]` on `AsdlDocument`.
- `global_parameters` are valid only in the entry file. Imported files that
  declare `global_parameters` produce an error.
- Add explicit global reference token syntax `!{name}` in instance parameter
  values (and other backend-rendered parameter contexts).
- All `!{name}` tokens must resolve to declared entry `global_parameters`.
  Unresolved references produce an error.
- Emit global parameter declarations immediately after `__netlist_header__`,
  before any first use, in deterministic declaration order.

Backend rendering policy:

- Declaration form is backend-owned (`.param`, `.PARAM`, `parameters`, etc.).
- Reference form is backend-owned (`{name}` for ngspice/xyce, `name` for
  spectre) via config-driven emission policy.

## Consequences

- Global parameters become explicit, inspectable, and validation-friendly.
- Module `parameters` remain subckt-interface semantics and are not overloaded.
- Import behavior stays simple: simulation environment is entry-owned.
- Requires coordinated updates across AST, lowering/validation, backend config,
  emission templating, diagnostics, and tests.

## Alternatives

- Auto-detect globals from unresolved tokens.
  - Rejected: typo-prone, non-deterministic, and backend-coupled.
- Reinterpret top-module `parameters` as globals when `--top-as-subckt` is off.
  - Rejected: mode-dependent semantics and confusing scope.
- Keep global params only as library devices (`sim.param`).
  - Rejected as canonical approach: workable but semantically indirect and
    harder to validate/tool across backends.
