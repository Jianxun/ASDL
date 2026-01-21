# Refactor Spec - Pattern Service and Binding

Status: Draft (refactor-only; not canonical)

## 1. Purpose
Define the pattern service API that parses, validates, binds, and expands
pattern expressions for PatternedGraph. All pattern semantics live here; graph
nodes only reference expression IDs.

## 2. Inputs and Outputs
Inputs:
- Raw pattern expression strings.
- Named pattern definitions (module-local).
- Optional axis tags for named patterns.

Outputs:
- Parsed PatternExpr values with axis metadata.
- BindingPlan structures for net-to-endpoint binding.
- Expanded atoms for emission or derived indices.

## 3. PatternExpr Model
```
PatternExpr {
  raw: str
  segments: list[PatternSegment]
  axes: list[AxisSpec]
  axis_order: list[AxisId]
  span: SourceSpan | None
}

PatternSegment {
  tokens: list[PatternToken]
  span: SourceSpan | None
}

AxisSpec {
  axis_id: str
  kind: "enum" | "range"
  labels: list[str | int]
  size: int
  order: int
}
```

Axis identity uses `axis_id` from the tagged pattern group or the named
pattern reference. Untagged groups have no axis_id and cannot participate in
named-axis broadcast.

## 4. Named Pattern References
Pattern references (`<@name>`) are module-local and expand to a single group
token. Axis rules:
- `axis_id = tag` when present, otherwise the pattern name.
- Duplicate `axis_id` within a single expression is an error.
- If multiple patterns share an `axis_id`, their expansion lengths must match.

## 5. Expansion Rules
Expansion follows the existing core rules:
- Splicing (`;`) splits segments and concatenates expansions.
- Enumeration (`|`) and ranges (`:`) expand left-to-right.
- Endpoint expressions expand as a whole, then each atom must contain exactly
  one `.` delimiter, which is split into instance and pin tokens.

## 6. Binding Rules (Named-Axis Broadcast)
Binding compares total expansion lengths; splicing is flattened.

Let `N` be the net expansion length and `E` be the endpoint expansion length.

If `N == E`, bind by index.

If `N != E`:
- If either expression contains an unnamed group, broadcast is disallowed.
- Otherwise, named-axis broadcast applies only when the net's axis_id sequence
  appears as a left-to-right subsequence of the endpoint's axis_id sequence.
- For any shared axis_id, sizes must match exactly.
- Endpoint expansion may be `N * K` where `K` is the product of the endpoint's
  extra axis lengths. Binding repeats the net list for each extra-axis
  combination in endpoint expansion order.

If the net is scalar (`N == 1`), it may bind to endpoints of any length; each
expanded endpoint binds to the single net.

## 7. BindingPlan
Binding results are captured in a plan for verification and emission.

```
BindingPlan {
  net_expr_id: ExprId
  endpoint_expr_id: ExprId
  net_length: int
  endpoint_length: int
  shared_axes: list[AxisId]
  broadcast_axes: list[AxisId]
  map_index: function(net_index, endpoint_index) -> int
}
```

`map_index` defines which net atom binds to a given endpoint atom.

## 8. Error Conditions (non-exhaustive)
- Duplicate axis_id within a single expression.
- Named patterns with conflicting axis_id lengths.
- Endpoint atoms without exactly one `.` delimiter.
- Binding mismatch when lengths differ and named-axis broadcast rules fail.
- Expansion exceeds configured maximum length (default 10k).
