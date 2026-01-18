# ASDL — Core Pattern Expansion Rules

This document defines the **minimal, mandatory pattern expansion rules** for ASDL.
Expansion is performed during parsing/elaboration to produce a fully explicit,
deterministic set of symbols and endpoint expressions.

This spec covers:
- numeric range expansion (`<start:end>`) using **`:`** inside `<...>`
- literal enumeration expansion (`<alt1|alt2|...>`) using **`|`** as delimiter
- splicing / parallel concatenation using **`;`**
- named pattern references (`<@name>`)

Wildcard matching, aliasing, and exporting syntax are intentionally excluded.

---

## 1. Design Principles

1. **Determinism**
   - Same input text → same expansion order → same expanded atoms

2. **YAML-friendly separators**
   - Avoid `,` in ASDL micro-syntax to eliminate quoting friction in YAML flow lists
   - Use `|` for alternatives, `;` for splicing

3. **Explicit joining**
   - Expansion performs literal concatenation with no implicit joiner

4. **Semantics are allowed**
   - Expansion is syntactic, but downstream tools may consume structural meaning
     (e.g. bus inference from indices, polarity pairing from alternatives).

---

## 2. Terms

- **Pattern expression**: full authored string (may include `;` and groups)
- **Pattern segment**: `;`-delimited piece of a pattern expression
- **Atom**: a single endpoint/name expression with no remaining pattern syntax;
  endpoint atoms may include a single `.` separator
- **Expansion**: mapping from a pattern expression to an ordered list of atoms
- **Pattern parts**: ordered substitution values chosen by pattern operators
  within a pattern segment, recorded per atom for provenance
- **Splice**: concatenation of expansions from multiple segments separated by `;`

---

## 3. Supported Pattern Forms

### 3.0 Named Pattern References: `<@name>`

Named patterns provide module-local aliases for single-group pattern tokens.

**Syntax (definition)**
```yaml
patterns:
  <name>: <pattern-group>
  <name2>:
    expr: <pattern-group>
    tag: <axis-id>
```

**Syntax (reference)**
```
<@name>
```

**Semantics**
- `<@name>` is replaced by the referenced **group token** (`expr`) before expansion.
- Substitution is purely textual and happens prior to any expansion or binding.
- Axis metadata (axis_id, source span) is recorded before substitution and used
  for binding checks and diagnostics.

**Rules**
- `patterns` are **module-local** only.
- Pattern names must match `[A-Za-z_][A-Za-z0-9_]*`.
- Pattern values must be a **single group token**: `<...>` using `|` for enums
  or `:` for ranges.
- Object patterns may use only `expr` (required) and `tag` (optional).
- `tag`, when present, must match `[A-Za-z_][A-Za-z0-9_]*`.
- `axis_id = tag` if present, otherwise `axis_id = pattern name`.
- If multiple patterns share an `axis_id`, their expansion lengths must match
  (validated at definition time).
- Named patterns must not reference other named patterns (no recursion).
- Undefined names are errors.

### 3.1 Numeric Range Expansion: `<start:end>`

**Syntax**
```
<base><start:end>
```

**Semantics**
- Expands into a sequence of atoms by appending numeric suffixes
- No implicit joiner is inserted between base and numeric suffix
- Range is **inclusive**
- Expansion order follows the written direction

**Examples**
```
DATA<3:0> → DATA3 DATA2 DATA1 DATA0
DATA_<3:0> → DATA_3 DATA_2 DATA_1 DATA_0
```

**Rules**
- `start` and `end` must be integers
- No implicit zero-padding
- No vector arithmetic is implied by the expander

---

### 3.2 Literal Enumeration Expansion: `<alt1|alt2|…>`

**Syntax**
```
<base><alt1|alt2|...>
```

**Semantics**
- Expands into one atom per listed alternative
- No implicit joiner is inserted between base and alternative literal
- Alternatives are substituted literally

**Examples**
```
OUT<P|N> → OUTP OUTN
BIAS_<A|B|C> → BIAS_A BIAS_B BIAS_C
SEL<digits> → SELdigits
```

**Rules**
- Alternatives are opaque literals (no implicit semantics at this stage)
- Whitespace around `|` is not allowed
- A single literal with no `|` is treated as a length-1 enum (e.g., `<digits>`)
- No nesting or recursion inside `<...>` in Tier-1 core

---

### 3.3 Splicing / Parallel Concatenation: `seg1;seg2;…`

**Syntax**
```
<segment>;<segment>;...
```

**Semantics**
- Each segment expands independently (using 3.1 and/or 3.2)
- The final expansion is the **ordered concatenation** of segment expansions,
  preserving segment order left-to-right

**Examples**
```
net1;net2_<2:0>
→ net1 net2_2 net2_1 net2_0

OUT_<P|N>;CLK_<1:0>
→ OUT_P OUT_N CLK_1 CLK_0
```

**Rules**
- `;` has the **lowest precedence** among Tier-1 pattern operators
- Whitespace around `;` is not allowed
- Empty segments are invalid

---

## 4. Expansion Order and Evaluation

- Pattern operators resolve **strictly left-to-right** within a segment.
- Each operator expands the current list and **concatenates** results in order.
- Splicing (`;`) splits segments; segments expand left-to-right and concatenate.
- Pattern operators may appear multiple times in a pattern expression; literal
  text between operators is preserved, so patterns can appear mid-expression.
- Expansion is single-pass; no recursive re-expansion.
- After expansion, no pattern syntax may remain.

---

## 5. Expansion Scope

- Patterns are allowed only in instance names, net names, and endpoint expressions
  (instance name and pin name).
- Patterns are forbidden in model names.
- Endpoint expressions use a single `.` delimiter (`inst.pin`). Expansion is
  applied to the full endpoint expression, then each expanded atom is split on
  `.` to recover instance and port names. Each expanded endpoint atom must
  contain exactly one `.`.
- `$` net names preserve pattern syntax verbatim; `;` is forbidden in `$` net
  expressions.
- Literal names must match `[A-Za-z_][A-Za-z0-9_]*` and must not contain
  pattern delimiters (`<`, `>`, `|`, `:`, `;`).
- Expansion is local to the pattern expression being expanded
- Expansion does not imply hierarchy or connectivity semantics by itself

---

## 6. Name Collision Rules

If expansion produces duplicate atoms *within the same expanded list*:
- Result is **invalid**
- This is a **hard error**
- No auto-renaming is permitted

---

## 7. Error Handling

| Condition | Behavior |
|---------|----------|
| Invalid numeric range syntax | Error |
| Empty enumeration (`<>` or `<|>`) | Error |
| Empty splice segment (`a;;b`) | Error |
| Duplicate expanded atoms | Error |
| Expansion exceeds 10k atoms per pattern expression | Error |
| Unexpanded pattern remains | Error |

---

## 8. Binding and Equivalence Rules (Pre-Elaboration)

- Binding compares **total expansion length**; splicing (`;`) is flattened into
  a single list with no segment alignment.
- Axis identity uses `axis_id` (tag if present, otherwise pattern name). Each
  `axis_id` may appear at most once per expression; duplicates are errors.
- If a net expands to length **N > 1**:
  - If the endpoint expands to **N**, binding is by index.
  - If the endpoint expands to a different length:
    - If either expression contains an unnamed group (`<...>` without `@`),
      broadcast is disallowed and the binding is an error.
    - Otherwise, **named-axis broadcast** applies only when the net's axis_id
      sequence appears as a left-to-right subsequence of the endpoint's axis_id
      sequence, and all shared axis_ids have equal lengths. If any check fails,
      the binding is an error.
    - When the checks pass, the endpoint may expand to **N * K** where **K** is
      the product of the endpoint's extra axis lengths. Binding repeats the net
      list for each extra-axis combination in endpoint expansion order.
- If a net is scalar (length **1**), it may bind to endpoints of any length;
  each expanded endpoint binds to that single net (endpoints may differ in
  length).
- Endpoint expansion length is computed from the full `inst.pin` expression;
  expand the full expression and split each atom on `.`. This is equivalent to
  **N * M** when the instance expands to **N** and the pin expands to **M**
  (left-to-right order).
- Instance name patterns and instance parameter patterns expand at the same time;
  parameter values zip by instance index (scalar broadcast allowed).
- Every scalar endpoint atom binds to **exactly one** net.
- Equivalence checks use the fully expanded string atoms (e.g., `MN<A|B>` is
  equivalent to `MN_A` and `MN_B`). Binding verification and elaboration must
  share the same equivalence helper.

### Examples

Valid broadcast with extra axis in the endpoint:

```yaml
patterns:
  cell: <99:0>
  pol: <p|n>
  bus: <7:0>

nets:
  net<@bus><@pol>: [cell<@cell><@bus>.<@pol>]
```

Valid broadcast with tagged axis identity across differing ranges:

```yaml
patterns:
  cell: <99:0>
  pol: {expr: <p|n>, tag: pol}
  pol_b: {expr: <n|p>, tag: pol}
  bus: <7:0>

nets:
  net<@bus><@pol>: [cell<@bus><@cell>.<@pol_b>]
```

Invalid broadcast when axis order breaks the subsequence rule:

```yaml
patterns:
  cell: <99:0>
  pol: <p|n>
  bus: <7:0>

nets:
  net<@bus><@pol>: [cell<@pol><@bus>.<@pol>]
```

---

## 9. Pattern Metadata for Atomized IR

- Atomized IR may attach `pattern_origin` metadata to each atom derived from a
  pattern expression.
- `pattern_origin` refers to a pattern expression table entry (expression string
  + source span) and records:
  - `segment_index`: the 0-based segment position within the expression
    (left-to-right).
  - `pattern_parts`: ordered substitution values used for this atom within the
    segment (operator occurrence order).
  - The pattern expression table lives in module attributes.

---

## 10. Semantics and Downstream Consumption (Allowed)

Downstream tools may interpret expanded structure, for example:
- infer bus widths / ordering from numeric suffixes
- infer polarity pairs from `<P|N>` style expansions
- group related atoms originating from a common base

Such interpretations are **optional and tool-defined** and must not change the
correctness of the expanded structural IR.

---

## 11. Explicit Non-Goals

- Wildcard or glob matching (`*`)
- Regex or predicate patterns
- Semantic aliasing / net merging
- Export / re-export mechanisms
- Implicit net creation
- Escaping or quoting pattern delimiters inside literal names

---

## 12. Post-Expansion Invariant

After expansion:
- Every endpoint/name is a plain atom (no `<...>`, no `;`)
- Every endpoint atom contains exactly one `.` delimiter
- No implicit joiner has been applied (atoms are literal concatenations)
- The result is suitable for deterministic validation and lowering
