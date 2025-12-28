# ASDL Compiler Architecture: Layered Responsibilities

This summarizes our agreed compiler architecture for ASDL, with **ruamel + pydantic as the front-end** and **xDSL as the semantic core**.  
The guiding principle is: **one semantic center, no duplicated truth**.

---

## High-level principle

> **xDSL IR is the single source of semantic truth.**  
> Everything before it prepares input; everything after it transforms or emits.

All other layers must be:
- local
- acyclic
- semantics-free (or semantics-light)
- replaceable without breaking correctness

---

## Layer 0 — Text & Concrete Syntax (YAML)

**Tool**: `ruamel.yaml`

### Responsibilities
- Parse YAML
- Preserve:
  - key order (if desired)
  - comments (optional)
  - source locations (line/column)
- Detect pure YAML errors:
  - syntax errors
  - duplicate keys
  - invalid scalars

### Explicit non-responsibilities
- No ASDL semantics
- No schema validation
- No symbol resolution
- No formatting decisions

This layer exists purely to bridge *text → structured data* with good diagnostics.

---

## Layer 1 — Formatting (optional but recommended)

**Tool**: YAML formatter (ruamel-based or external)

### Responsibilities
- Canonicalize *textual form*:
  - indentation
  - block vs flow (choose canonical output)
  - quoting style
- Ensure idempotence (format twice → no diff)

### Key decision (ASDL)
- **Accept both block and flow styles as input**
- **Emit block style as canonical output**
- Flow style is input sugar only; semantics do not depend on it

### Explicit non-responsibilities
- No schema awareness
- No ASDL meaning
- No validation

Formatting happens **before parsing into AST** because AST intentionally forgets syntax.

---

## Layer 2 — ASDL AST / Shape Gate

**Tool**: `pydantic`

### Responsibilities
Pydantic is a **typed YAML boundary**, not a compiler phase.

It enforces:
- Required fields exist
- Field types are correct
- Tagged unions / enums
- Local constraints (e.g. positivity, naming regex)
- Defaults and normalization
- Canonical Python data structures

Example:
- `instance.model` is **just a string**
- `pins` is `dict[str, str]`
- Flow vs block pins normalize to the same dict

### What pydantic explicitly does NOT do
- No symbol resolution
- No name lookup
- No connectivity checks
- No hierarchy validation
- No imports / dependency injection
- No ERC
- No cross-object validation

### Mental model
> **Pydantic answers: “Is this valid ASDL *syntax*?”**  
> **Not: “Is this a valid *circuit*?”**

If pydantic were removed tomorrow, correctness would remain — only error quality would degrade.

---

## Layer 3 — Lowering (ASDL → xDSL IR)

**Tool**: Custom lowering code

### Responsibilities
- Convert AST objects into xDSL dialect ops
- Attach source locations (from ruamel)
- Preserve author intent without enforcing correctness
- Produce IR even if semantically wrong

Key transformations:
- Strings → symbol references
- Implicit structure → explicit ops
- YAML hierarchy → IR hierarchy/graph

Lowering **must not crash** on bad designs; it must emit IR + diagnostics later.

---

## Layer 4 — xDSL IR (Semantic Core)

**Tool**: xDSL dialect(s)

### Responsibilities
This is where **all circuit semantics live**.

- Symbol tables
- Name resolution
- Connectivity graph
- Directionality
- Hierarchy consistency
- Primitive pin requirements
- Imports / dependency injection
- Template elaboration
- Canonical circuit representation

### ERC lives here
ERC-style checks belong to:
- **Op verifiers** (local invariants)
- **IR passes** (global / cross-hierarchy checks)

Examples:
- dangling pins
- unconnected nets
- pin ↔ net collisions
- mismatched module interfaces
- illegal primitive usage

This mirrors ERC vs LVS separation in EDA.

---

## Layer 5 — Passes, Lowering, Emission

**Tool**: xDSL passes

### Responsibilities
- Elaboration (templates, hierarchy)
- Normalization
- Lowering to:
  - netlists
  - schematics
  - simulators
  - layout flows

At this point, the design is fully explicit and analyzable.

---

## Summary Table

| Layer | Purpose | Knows semantics? | Knows symbols? | Can reject design? |
|---|---|---|---|---|
| YAML | Text parsing | ❌ | ❌ | ❌ |
| Formatter | Text canonicalization | ❌ | ❌ | ❌ |
| Pydantic | Shape & types | ❌ (local only) | ❌ | ✅ (syntax only) |
| Lowering | Structure mapping | ❌ | 🔶 (refs only) | ❌ |
| xDSL IR | Semantic truth | ✅ | ✅ | ✅ |
| Passes | Transform & emit | ✅ | ✅ | ✅ |

---

## Architectural invariant (the anchor)

> **Pydantic carries *strings*.  
> xDSL carries *meaning*.**

Keeping this boundary strict is what prevents semantic duplication and long-term tech debt.
