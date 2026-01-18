# ADR-0020: Tagged pattern axes for broadcast binding

Status: Proposed

## Context
Named pattern broadcast currently keys axis identity to the literal pattern name.
This blocks common fanout cases where two axes are logically the same but use
different ranges (for example `<25:1>` vs `<24:0>`). We want explicit,
module-local axis identity without introducing implicit or ambiguous broadcast.

## Decision
Introduce tagged pattern definitions that decouple axis identity from the range
expression, and use axis identity to drive broadcast matching with explicit
failures on mismatches.

### Pattern definition schema
Patterns remain module-local and are still referenced as `<@NAME>`. A pattern
definition may now be:
- a string group token (existing behavior), or
- an object with metadata:

```yaml
patterns:
  BUS25: <25:1>
  BUS0:
    expr: <24:0>
    tag: BUS
```

Rules:
- `expr` is required for object patterns and must be a single group token.
- `tag` is optional; when present it must be a literal name.
- `axis_id = tag` if present, otherwise `axis_id = pattern name`.
- Axis identity is module-local; cross-module collisions are irrelevant.

### Broadcast matching rules
Let the net expression have named pattern groups with axis_ids
`A_net = [a1, a2, ...]` and lengths `L_net = [l1, l2, ...]` in left-to-right
expression order. Let the endpoint expression have `A_end` and `L_end` in the
same sense.

Broadcast eligibility and checks:
1. Broadcast is considered only when the net length `N > 1` and **all** pattern
   groups on both sides are named (`<@name>`). If any unnamed group appears on
   either side, the strict length rules apply and no broadcast is attempted.
2. Each `axis_id` must appear **at most once** per expression; duplicates are an
   error.
3. For every `axis_id` that appears in both net and endpoint expressions, the
   associated lengths must be equal; otherwise, error.
4. `A_net` must appear as a left-to-right subsequence of `A_end`; otherwise,
   error.

Binding semantics when the checks pass:
- The endpoint expands in canonical left-to-right axis order.
- Each expanded endpoint atom is associated with its axis coordinate tuple.
- Project that tuple onto the net axes (`A_net`) by axis_id; the projected
  coordinates select the matching element in the net expansion list.
- This is equivalent to repeating the net list across all combinations of the
  endpoint's extra axes in endpoint expansion order.

Scalar net binding remains unchanged: a net that expands to length 1 may bind to
endpoints of any length.

### Diagnostics
Broadcast mismatches are **hard errors** (no fallback). Diagnostics must include
the offending pattern token (`<@NAME>`) and its source span; for length/order
conflicts, label both sides when possible.

## Consequences
- Enables explicit bus fanout across differently indexed patterns.
- Adds AST/schema surface area (tagged patterns) and requires axis metadata
  propagation for diagnostics.
- Mismatched named-group axes now emit explicit errors instead of silently
  degrading to strict-length binding.

## Alternatives
- Implicit broadcast when lengths divide evenly: rejected due to ambiguity.
- Grammar-level broadcast markers: rejected due to positional fragility.
