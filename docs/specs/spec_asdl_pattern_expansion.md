# ASDL — Core Pattern Expansion Rules

This document defines the **minimal, mandatory pattern expansion rules** for ASDL.
Expansion is performed during parsing/elaboration to produce a fully explicit,
deterministic set of symbols and endpoint tokens.

This spec covers:
- numeric range expansion (`[...]`)
- literal enumeration expansion (`<...>`) using **`|`** as delimiter
- splicing / parallel concatenation using **`;`**

Wildcard matching, aliasing, and exporting syntax are intentionally excluded.

---

## 1. Design Principles

1. **Determinism**
   - Same input text → same expansion order → same expanded tokens

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

- **Atom**: a single endpoint/name token with no remaining pattern syntax
- **Expansion**: mapping from a pattern expression to an ordered list of atoms
- **Splice**: concatenation of expansions from multiple segments separated by `;`

---

## 3. Supported Pattern Forms

### 3.1 Numeric Range Expansion: `[start:end]`

**Syntax**
```
<base>[start:end]
```

**Semantics**
- Expands into a sequence of atoms by appending numeric suffixes
- No implicit joiner is inserted between base and numeric suffix
- Range is **inclusive**
- Expansion order follows the written direction

**Examples**
```
DATA[3:0] → DATA3 DATA2 DATA1 DATA0
DATA_[3:0] → DATA_3 DATA_2 DATA_1 DATA_0
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
- No implicit joiner is inserted between base and alternative token
- Alternatives are substituted literally

**Examples**
```
OUT<P|N> → OUTP OUTN
BIAS_<A|B|C> → BIAS_A BIAS_B BIAS_C
```

**Rules**
- Alternatives are opaque tokens (no implicit semantics at this stage)
- Whitespace around `|` is not allowed
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
net1;net2_[2:0]
→ net1 net2_2 net2_1 net2_0

OUT_<P|N>;CLK_[1:0]
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
- Expansion is single-pass; no recursive re-expansion.
- After expansion, no pattern syntax may remain.

---

## 5. Expansion Scope

- Patterns are allowed only in instance names, net names, and endpoint tokens
  (instance name and pin name).
- Patterns are forbidden in model names.
- `$` net names preserve pattern tokens verbatim; `;` is forbidden in `$` net
  expressions.
- Literal names must match `[A-Za-z_][A-Za-z0-9_]*` and must not contain
  pattern delimiters (`<`, `>`, `[`, `]`, `;`).
- Expansion is local to the token being expanded
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
| Expansion exceeds 10k atoms per token | Error |
| Unexpanded pattern remains | Error |

---

## 8. Binding and Equivalence Rules (Pre-Elaboration)

- Binding compares **total expansion length**; splicing (`;`) is flattened into
  a single list with no segment alignment.
- If a net expands to length **N > 1**, every bound endpoint token must expand
  to **N**; binding is by index.
- If a net is scalar (length **1**), it may bind to endpoints of any length;
  each expanded endpoint binds to that single net (endpoints may differ in
  length).
- Endpoint expansion length is computed from the full `inst.pin` token; if the
  instance expands to **N** and the pin expands to **M**, the endpoint expands
  to **N * M** (left-to-right order).
- Every scalar endpoint atom binds to **exactly one** net.
- Equivalence checks use the fully expanded string tokens (e.g., `MN<A,B>` is
  equivalent to `MN_A` and `MN_B`). Binding verification and elaboration must
  share the same equivalence helper.

---

## 9. Semantics and Downstream Consumption (Allowed)

Downstream tools may interpret expanded structure, for example:
- infer bus widths / ordering from numeric suffixes
- infer polarity pairs from `<P|N>` style expansions
- group related atoms originating from a common base

Such interpretations are **optional and tool-defined** and must not change the
correctness of the expanded structural IR.

---

## 10. Explicit Non-Goals

- Wildcard or glob matching (`*`)
- Regex or predicate patterns
- Semantic aliasing / net merging
- Export / re-export mechanisms
- Implicit net creation
- Escaping or quoting pattern delimiters inside literal names

---

## 11. Post-Expansion Invariant

After expansion:
- Every endpoint/name is a plain atom (no `[]`, no `<>`, no `;`)
- No implicit joiner has been applied (atoms are literal concatenations)
- The result is suitable for deterministic validation and lowering
