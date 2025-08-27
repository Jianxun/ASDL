# ASDL Language Semantics (v0.5)

This document defines the syntactic and semantic rules that govern the ASDL YAML format.
These rules ensure structural consistency and enable LLMs and tools to parse and reason about analog designs.


---
## Introduction

Analog Structural Description Language (ASDL) is a declarative, YAML-based format designed to capture analog circuit topologies with explicit design intent, modular hierarchy, and symmetry-aware structures. Unlike traditional netlists, ASDL emphasizes human- and machine-readable semantics, making it ideal for AI-assisted workflows, version-controlled design iteration, and reusable IP representation. It supports pattern expansions for differential and bus structures, integrates directly with PDK device lines, and enables metadata annotations for layout, matching, and operating point specifications—bridging the gap between schematic abstraction and simulation-ready output.

---

## 📌 Pattern Expansion Syntax

ASDL supports two types of pattern expansion:

### 1. Literal Expansion — `<a,b,c>`
Used for:
- Polarity (e.g., `p,n`)
- Symmetric layouts (e.g., `tl,tr,bl,br`)

Expands:
```
in_<p,n> → in_p, in_n
M_<1,2,3> → M_1, M_2, M_3
```

Used in:
- Ports
- Nets
- Instance names
- Mappings (only on values)

---

### 2. Numerical Bus Expansion — `[N:M]`
Used for:
- Buses, arrays, vectorized nets

Expands:
```
out[3:0] → out[3], out[2], out[1], out[0]
```

Supports descending and ascending order.

Used in:
- Ports
- Nets
- Instances
- Mappings (only on values)

---

## 🔄 Mapping Rules

Mappings follow **order-based matching** between expanded keys and values.

- **Expansion only on the RHS**.
- LHS expansion is **implicitly derived** from the instance name pattern.

### ✅ Valid:
```yaml
instances:
  MN_<p,n>:
    model: nmos_unit
    mappings:
      D: out_<n,p>    # Order-matched
      G: in_<p,n>     # One model port mapped to each expanded net
      S: tail         # Broadcast scalar to all instances
```

### ❌ Invalid:
```yaml
mappings:
  D_<p,n>: out_<n,p>  # ❌ LHS expansion is not allowed; causes port mismatch
```

---

## 🧠 Substitution and Evaluation

- Parameters can be referenced using `$param` inside expressions.
- Parameter values can be expressions evaluated by ngspice or other backends.
- Use explicit types and units to enable static checking.

---

## 🧱 Optional Metadata (via `metadata` block)

Metadata is useful for LLMs, layout tools, and design automation.

```yaml
metadata:
  design_intent:
    gm_over_Id: 15
    region: saturation
    nominal_current: 50e-6
  layout:
    type: common_centroid
    symmetry: diff
    match_group: tail_mirror
```

---

## ✅ Best Practices

- Use `doc:` fields consistently to annotate all design elements.
- Prefer one-line port definitions for simple cases; expand to multi-line if constraints grow.
- Keep parameter names concise and meaningful.
- Use `<p,n>` for symmetric design elements; use `[N:0]` for buses.

---

## 🔍 Future Extensions (planned)

- Behavioral model stubs using dependent sources
- Support for testbench specification files
- Visual layout hints (e.g., horizontal rails, grid constraints)