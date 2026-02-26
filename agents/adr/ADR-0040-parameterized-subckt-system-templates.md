# ADR-0040: Parameterized Subckt System Templates

**Status**: Proposed  
**Date**: 2026-02-26

## Context

Simulation backends require different syntax for parameterized subcircuit
headers and calls (for example keyworded vs non-keyworded call forms). We need
simulation-only parameterized subckts without hardcoding backend-specific
quirks in compiler logic.

Existing system devices (`__subckt_header__`, `__subckt_call__`) model
non-parameterized module syntax, but do not provide explicit backend-owned
forms for parameterized subckt declarations/calls.

## Decision

Introduce two required parameterized system-device templates for each backend:

- `__subckt_header_params__`
- `__subckt_call_params__`

Compiler behavior remains backend-agnostic:

- select `__subckt_header_params__` when a subckt header has parameters,
  otherwise `__subckt_header__`
- select `__subckt_call_params__` when a module instance has parameters,
  otherwise `__subckt_call__`

`{params}` is rendered as deterministic, space-delimited `key=value` tokens in
stable parameter order. Backend-specific keywords/wrappers must be expressed in
template strings (for example `PARAMS: {params}`), not compiler conditionals.

## Consequences

- Backend syntax differences are fully owned by backend configuration templates.
- Emitter policy is simpler to reason about: only parameter-presence dispatch,
  no backend-name branching.
- Every backend now has a larger required template set and must define the two
  new parameterized system-device entries.

## Alternatives

- Keep one `__subckt_*` template and add backend-specific `params_clause`
  compiler logic.
  - Rejected: leaks backend quirks into compiler code paths.
- Introduce plugin hooks per backend for subckt rendering.
  - Rejected: flexible but shifts behavior from declarative config to code and
    increases maintenance/safety overhead.
