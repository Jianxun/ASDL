# ADR-0019: Named Pattern Broadcast Binding

Status: Proposed

## Context
The current binding rules require endpoint expansion length to match net
expansion length when a net expands to length > 1. This blocks common
hierarchical bus fanout cases such as broadcasting a 25-bit bus to 130 row
instances in a switch matrix. Named patterns (`<@name>`) already provide
explicit, shared pattern groups across expressions, but the binding rules do
not yet leverage them for broadcasting.

## Decision
- Extend binding rules to allow **named-pattern broadcast** for non-scalar nets.
- A net expression may bind to an endpoint expression with extra axes **only
  when both expressions use named pattern groups** and the net's named groups
  appear in the endpoint in the same left-to-right order.
- Broadcast is **explicit**: no length-based inference. If the net or endpoint
  uses any unnamed pattern group (`<...>` without `@`), the existing strict
  length rule applies.
- Binding semantics:
  - Let the net expand to an ordered list `N` of length `L`.
  - Let the endpoint expand to `E` of length `L * K`, where `K` is the product
    of lengths of the endpoint's extra named groups (those not present in the
    net).
  - Bind by repeating `N` for each combination of extra-axis values, following
    the endpoint expansion order (left-to-right within the expression).
- Example (valid):
  ```yaml
  patterns:
    ROW: <130:1>
    BUS: <25:1>
  nets:
    $BUS<@BUS>: [sw_row<@ROW>.BUS<@BUS>]
  ```

## Consequences
- Enables concise, explicit bus fanout while avoiding ambiguous length-based
  broadcasts.
- Requires binding verification and elaboration to track named pattern groups
  (axis order) and apply the broadcast mapping.
- Authors must use named patterns for broadcast; anonymous ranges keep strict
  length matching.

## Alternatives
- Implicit broadcast when lengths divide evenly: rejected due to ambiguity and
  accidental acceptance of unintended bindings.
- Allow general arithmetic in patterns (e.g., `N_ROW-1`): rejected for now due
  to parser and verification complexity.
