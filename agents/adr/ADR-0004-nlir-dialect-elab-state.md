# ADR-0004: NLIR dialect and elaboration state

- Status: Accepted
- Date: 2026-01-01

## Context
- ASDL_NLIR exists in unelaborated and elaborated forms, but MVP treats them as structurally identical.
- Using separate dialects (`asdl_nlir_u`/`asdl_nlir_e`) risks drift and duplicated tooling.
- We still need a durable, explicit signal for elaboration state.

## Decision
- Use a single xDSL dialect `asdl_nlir` for both ASDL_NLIR_U and ASDL_NLIR_E.
- Represent elaboration state via an explicit attribute (`elab_state = "u" | "e"`), required on top-level containers and consistent within a design.
- Keep ASDL_NLIR_U/E as semantic IR IDs in specs and docs.

## Consequences
- Tooling, tests, and emitters target one dialect; U/E is a validated state flag.
- No mixing of U/E within a single design; validators enforce consistency.
- If U/E diverge later, we can extend the dialect while preserving the state flag.

## Alternatives
- Separate dialects per state (`asdl_nlir_u`, `asdl_nlir_e`) — rejected; higher maintenance and risk of divergence.
- Single dialect without explicit state — rejected; loses a checkable contract and complicates debugging.
