# ADR-0039: Shared Top-Resolution Policy Helper

- Status: Proposed
- Date: 2026-02-26

## Context
Top-module resolution semantics currently appear in multiple places
(`core.hierarchy`, `emit.netlist.ir_utils`, and views/query-adjacent code).
These implementations are similar but not centrally owned, which creates drift
risk for ambiguity handling and entry-file constraints.

Emission requires strict, diagnostic-producing behavior (`EMIT-001`) for
ambiguous or missing top resolution. Traversal/query/views need the same core
selection semantics but typically operate in permissive, non-fatal mode.

## Decision
Adopt a single shared top-resolution policy helper under `src/asdl/core/`
consumed by both traversal and emission code paths.

1. Introduce one canonical helper that resolves top module selection with
   explicit policy controls (strict vs permissive; entry-file enforcement).
2. `asdl.core.hierarchy` and traversal/query/view callers must use permissive
   policy and return empty/no-result behavior when top cannot be resolved.
3. `asdl.emit.netlist` must use strict policy and preserve existing
   diagnostic contract (`EMIT-001` cases and user-facing behavior).
4. Existing duplicated top-resolution helpers must be removed after migration.

## Consequences
- Positive: one source of truth for top selection semantics and fewer drift
  regressions.
- Positive: preserves intended UX split (inspection flows non-fatal, emission
  strict and diagnostic-driven).
- Tradeoff: requires a small migration across core and emit modules plus
  regression updates.

## Alternatives
- Keep independent top-resolution logic in each subsystem: rejected due to
  repeated drift and maintenance overhead.
- Fully couple traversal to emitter-only strict logic: rejected because query
  and view inspection paths should not hard-fail on unresolved top.
