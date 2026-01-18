# Option A Summary: Tagged Patterns with String-or-Object Syntax

**Goal**  
Enable explicit, unambiguous bus broadcasting between differently indexed patterns (e.g. `<25:1>` ↔ `<24:0>`) while preserving existing authoring ergonomics.

**Key Idea**  
Decouple **axis identity** from **range expression** by adding an optional **tag** to pattern definitions.  
Broadcast matching uses **tags**, not literal pattern names.

**Authoring Model**
- `patterns.<name>` may be either:
  - a **string** (existing behavior), or
  - an **object** with metadata.

```yaml
patterns:
  ROW: <130:1>          # unchanged
  BUS25: <25:1>         # unchanged
  BUS0:
    expr: <24:0>
    tag: BUS
```

**Resolution Rules**
- For string patterns:
  - `expr = string`
  - `axis_id = pattern name`
- For object patterns:
  - `expr = expr`
  - `axis_id = tag`
- Pattern length is always derived from `expr`.

**Backwards Compatibility**
- Existing designs require no changes.
- Tags are only needed when axis identity must be shared across different ranges.

---

# ADR-0019: Tagged Pattern Broadcast Binding

**Status:** Proposed

## Context
ASDL currently requires endpoint expansion length to exactly match net expansion
length when a net expands to more than one element. This blocks common hierarchical
fanout cases, such as broadcasting a multi-bit bus to many row instances in a
switch matrix.

Named pattern groups (`<@NAME>`) already provide explicit expansion axes, but
their identity is currently tied to the literal pattern name. This prevents
broadcasting between logically equivalent axes that use different index
conventions (e.g. `<25:1>` vs `<24:0>`).

## Decision
Introduce **pattern tags** to define axis identity independently from the pattern
range expression, and use tags to drive explicit broadcast binding.

### Pattern Definition
- A pattern definition may be:
  - a **string expression**, or
  - an **object** with metadata.

```yaml
patterns:
  BUS25: <25:1>
  BUS0:
    expr: <24:0>
    tag: BUS
```

- Each pattern has:
  - an expansion expression (`expr`)
  - an **axis identifier**:
    - `axis_id = tag` if present
    - otherwise `axis_id = pattern name`

### Broadcast Eligibility
A net expression may bind to an endpoint expression with extra axes **only if**:

1. The net expands to length `L > 1`.
2. **All** pattern groups on both sides are named (`<@...>`).
3. For each pattern group, its `axis_id` is well-defined.
4. The sequence of net `axis_id`s appears as a **left-to-right subsequence** of
   the endpoint `axis_id`s.
5. For every shared `axis_id`, the corresponding pattern lengths are equal.
6. Each `axis_id` appears at most once per expression.

If any unnamed pattern group (`<...>` without `@`) appears on either side, or if
any of the above checks fail, binding reverts to **strict length equality**.

### Binding Semantics
- Let the net expand to an ordered list `N` of length `L`.
- Let the endpoint expand to an ordered list `E` of length `L × K`, where `K` is
  the product of the lengths of endpoint axes whose `axis_id`s do not appear in
  the net.
- Binding is performed by **axis projection**:
  - Each endpoint element is associated with a coordinate tuple over its axes.
  - That tuple is projected onto the net’s axis set (by `axis_id`).
  - The resulting coordinates select the corresponding element in `N`.

Expansion order is the canonical left-to-right axis expansion order used elsewhere
in ASDL.

### Example (Valid)
```yaml
patterns:
  ROW: <130:1>
  BUS25: <25:1>
  BUS0:
    expr: <24:0>
    tag: BUS

nets:
  $BUS<@BUS25>: [sw_row<@ROW>.BUS<@BUS0>]
```

This binds each of the 25 bus bits to all 130 row instances, despite differing
index conventions.

### Example (Invalid)
```yaml
$BUS<25:1>: [sw_row<@ROW>.BUS<@BUS0>]   # unnamed net pattern ⇒ strict length rule
```

## Consequences
- Enables concise, explicit bus fanout across differently indexed patterns.
- Preserves existing semantics for unnamed and untagged patterns.
- Requires elaboration to track `axis_id` per pattern group and enforce
  subsequence and length checks.
- Improves diagnostics by allowing axis-aware error reporting.

## Alternatives Considered
- Implicit broadcast when lengths divide evenly: rejected due to ambiguity.
- Grammar-level broadcast markers: rejected due to positional fragility.
- General arithmetic or index transforms in patterns: deferred due to complexity.

---
```
