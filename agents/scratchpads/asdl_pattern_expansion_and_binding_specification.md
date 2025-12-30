# ASDL Pattern Expansion and Binding Rules (v0)

This document defines the **normative semantics** for pattern expansion, instance grouping, and pin binding in ASDL. These rules are **compiler contracts**, enforced by elaboration, validation, and linting passes. No behavior outside this document is implicit.

---

## 1. Core Expansion Model

### 1.1 Expansion Produces Lists
All identifier expressions expand to a **flat, ordered list of scalar identifiers**.

- No vectors
- No implicit structure
- Only ordered lists

---

## 2. Expansion Operators

### 2.1 Literal Expansion
```
X<p,n>
→ [X_p, X_n]
```

- Literals append as suffixes
- Order is exactly as written

---

### 2.2 Bus Expansion
```
X[7:0]
→ [X_7, X_6, X_5, X_4, X_3, X_2, X_1, X_0]
```

- Range direction is semantic
- Index appends as suffix
- Ordering is deterministic

---

### 2.3 Nested Expansion Rule (Critical)

> **Each expansion operator duplicates the entire current list.**  
> **Operators apply strictly left-to-right.**  
> **Suffixes are append-only.**

Example:
```
tap<p,n>[7:0]
```

Expansion:
1. `tap` → `[tap]`
2. `<p,n>` → `[tap_p, tap_n]`
3. `[7:0]` duplicates the entire list per index

Final:
```
[tap_p_7, tap_n_7, tap_p_6, tap_n_6, …, tap_p_0, tap_n_0]
```

Changing operator order changes semantics:
```
tap[7:0]<p,n>
→ [tap_7_p, tap_7_n, tap_6_p, tap_6_n, …]
```

---

## 3. Tuple Lists

```
(A, B, C)
```

- Each element expands independently
- Result is **literal concatenation** of lists
- No zipping
- No broadcasting
- No reshaping

Example:
```
(in, node[7:1])
→ [in, node_7, node_6, …, node_1]
```

---

## 4. Group Expansion (Instances)

Example:
```
RS[7:0]<p,n>
```

- Expands using the same rules as identifiers
- Produces a list of instances
- Group size = product of expansion dimensions

```
len(RS[7:0]<p,n>) = 8 × 2 = 16
```

- Instance order is semantic and canonical

---

## 5. Pin Binding Rules

### 5.1 Named Binding Only

- **Positional / locational binding is forbidden**
- All bindings use explicit pin names

Canonical internal form:
```
pin_name → list_of_nets
```

---

### 5.2 Binding Length Rule (Non-negotiable)

For a group of size `N`:

- RHS expands to length `N` → elementwise binding
- RHS expands to length `1` → scalar broadcast
- Anything else → **compile error**

No implicit reshaping. No zipping.

---

### 5.3 Elementwise Binding

If RHS length = `N`:
```
instance[i].pin ← rhs_list[i]
```

Indexing follows canonical expansion order.

---

## 6. Broadcasting Rules

### 6.1 Implicit Broadcast (Restricted)

Allowed case only:
```
1 → N
```

- RHS expands to exactly one scalar
- Scalar duplicated to match group size

Example:
```
Minus: VSS
→ [VSS × N]
```

---

### 6.2 What Is NOT Implicitly Broadcast

Implicit broadcast is **forbidden** if RHS expands to:
- more than one element
- any pattern (`<…>`, `[…]`, `(…)`)

These require explicit repetition.

---

### 6.3 Explicit Broadcast: `repeat(expr, N)`

Definition:
```
repeat(expr, N)
```

- Expands `expr` to a list
- Repeats that list `N` times
- No suffixes added
- Order preserved

Examples:
```
repeat(VSS, 16)
→ [VSS ×16]

repeat(Vcm<p,n>, 8)
→ [Vcm_p, Vcm_n, Vcm_p, Vcm_n, …]
```

---

## 7. Error Conditions (Lint + Compile)

### 7.1 Length Mismatch

If:
```
len(rhs) ≠ 1 and len(rhs) ≠ len(group)
```
→ **error**

---

### 7.2 Identifier Collisions

If expansion produces an identifier already defined in the same scope:
→ **error**

No auto-renaming.

---

### 7.3 Malformed Patterns

Lint errors (often fatal):
- unmatched `< >`
- unmatched `[ ]`
- empty `< >`
- malformed ranges `[a:b]`
- YAML token splits caused by unquoted commas

---

## 8. YAML Interaction Rules

### 8.1 Block Style Is Canonical

Preferred:
```yaml
Minus: tap<p,n>[7:0]
```

---

### 8.2 Flow Style Requires Quoting

In `{}` or `[]`, scalars containing `<` or `,` **must be quoted**:
```yaml
Pins: ['tap<p,n>[7:0]', 'foo']
```

---

### 8.3 Linter Responsibility

The linter MUST warn on:
- unquoted `<p,n>` in flow style
- suspicious token splits
- unmatched pattern delimiters

Users *will* forget quotes. Catch it early.

---

## 9. Design Philosophy

- Correct by construction
- No implicit shape inference
- Order is semantic
- Agents must not guess
- Ambiguity surfaces as errors

---

This specification defines the **minimal, stable semantic core** for ASDL pattern expansion and binding. All future extensions must preserve these guarantees.

