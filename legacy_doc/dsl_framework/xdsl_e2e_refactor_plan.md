Got it — let’s lock scope to a **minimal, end-to-end pipeline** (AST → xDSL IR → passes → SPICE) and keep the AST-edit + graph features as clean add-ons later. Below is a tight plan that gets you back to a working compiler quickly, with small “future hooks” so you won’t have to rip things up later.

# E2E-first plan (pragmatic & minimal)

## Phase A — Dialect scaffold & IR dump (1–2 days)

**Goal:** print a valid textual IR from a tiny design.

* **Dialect**: `ModuleOp`, `InstanceOp`, `WireOp`, `PortAttr`, `RangeAttr`, `ExprAttr` (unresolved values).
* **Symbols**: make `ModuleOp` a symbol; `InstanceOp.callee` as a `SymbolRefAttr`.
* **Locations**: attach file:line:col; this also future-proofs diagnostics.
* **CLI**: `asdlc ir-dump` with `--verify`.
* **Tests**: one golden IR for `ota_5t` *pre-expansion*.

**Future hook kept:** `ExprAttr` (so later we can resolve vars/env without changing op schemas).

---

## Phase B — Expansion & resolution passes (2–4 days)

**Goal:** produce a fully concrete IR (no patterns or unresolved exprs).

* **PatternExpansionPass**: expand `<p,n>` and `[msb:lsb]` across ports, wires, instances. Deterministic naming (`net[p]→net_p`, `bus[3]→bus_3`).
* **VariableResolutionPass**: fold `ExprAttr` using module `variables` and parameter scope → `IntegerAttr`/`FloatAttr`.
* **EnvVarPass**: resolve `${VAR}`; emit diagnostics on missing values.
* **Verifiers (lightweight)**:

  * `InstanceOp`: pin count matches callee; pin names valid.
  * `WireOp`: width absent after expansion; forbid duplicates.
* **CLI**: `--run-pass pattern,var,env`.
* **Tests**: goldens for (a) pattern expansion, (b) var/env folding.

**Future hook kept:** stable, deterministic name canonicalization (you’ll reuse this for graphs later).

---

## Phase C — Validation (1–2 days)

**Goal:** catch structural issues before codegen.

* **Checks** (as verifiers/analyses, not transforms):

  * Port mapping sanity (instance pins ↔ callee ports).
  * Parameter override shape (unknown keys, type mismatch).
  * Missing nets / floating mandatory pins (configurable).
* **Diagnostics**: add IDs (e.g., `ASDL.E001`) + source ranges via `FusedLoc` where duplication happened.
* **Tests**: negative cases with stable error text + IDs.

**Future hook kept:** diagnostic IDs and fused locations make agent explanations trivial later.

---

## Phase D — SPICE lowering (2–4 days)

**Goal:** generate working SPICE from concrete IR.

* **Simplest path (recommended now)**: **direct emitter from ASDL IR**:

  * Traverse `ModuleOp` → emit `.subckt name ports...`
  * Emit `WireOp` comments (optional)
  * Emit `InstanceOp` lines using `params` and ordered `pins`
  * End with `.ends`
* **Optional (nice, not required now)**: a tiny `netlist` dialect as an intermediate; you can add this later without changing front half.
* **CLI**: `asdlc netlist --engine xdsl`.
* **Parity tests**: compare **legacy SPICE text** vs **IR-generated SPICE** on:

  * `examples/libs/ota_single_ended/ota_5t/`
  * `examples/libs/ota_single_ended/miller_ota/`

**Future hook kept:** the emitter takes a **connectivity table** (inst, pin → net) that you can re-use for graph export later.

---

# Minimal spec you need right now

* **ModuleOp**
  attrs: `{name, parameters:DictAttr, variables:DictAttr, spice_template?:StringAttr}`
  type: holds port list via `PortAttr[]` on the op (simple now; you can move to a type later).
  traits: symbol.

* **PortAttr**
  `{name, dir:(in|out|inout), kind:(analog|digital)}`
  *(You can add `supply|bulk` later—don’t block yourself now.)*

* **WireOp**
  `{name, width?:IntegerAttr|RangeAttr}` (width disappears post-expansion)

* **InstanceOp**
  `{sym_name, callee:SymbolRefAttr, params:DictAttr, pins:ArrayAttr<StringAttr>}`
  operands: variadic to `WireOp` (order matches `pins`).

* **ExprAttr**
  wraps unresolved expressions so Phase B can fold them.

That’s it. No new primitive-specific ops yet, no connect op, no hierarchy flattener. Keep it lean.

---

# Definition of Done (compiler functional again)

1. `asdlc ir-dump` prints valid IR for `ota_5t` and `miller_ota`.
2. `asdlc ir-dump --run-pass pattern,var,env --verify` succeeds on both.
3. `asdlc netlist --engine xdsl` emits SPICE; **parity diff** vs legacy is identical modulo whitespace/order (use normalized printers).
4. CI runs on macOS + Ubuntu (Py 3.10/3.11), with goldens for IR and SPICE.
5. Performance sanity: end-to-end runtime within 2× of legacy on those examples (informational).

---

# Risks you avoid (by scoping)

* **SSA complexity**: you’re staying with `WireOp` + operands; no multi-result devices.
* **Over-modeling pins**: you defer `supply|bulk` kinds and primitive roles until the generator/validator needs them.
* **Interop churn**: no MLIR bridge or netlist dialect yet.

---

# Tiny “future-proof” stubs to add now (no overhead)

* **`cref` string on AST nodes** (path-like ID). Just generate and store; don’t use it yet.
* **`ir_digest` helper**: SHA1 of canonical IR print; store in `out/meta.json` next to SPICE.
* **`--print-after each`** in CLI for quick debugging (mirrors `mlir-opt` feel).

These three give you plug-and-play anchors for the later AST-edit and graph export work without touching the E2E pipeline.

---

If you want, I can draft the minimal xDSL op classes and a 40-line SPICE emitter skeleton you can drop in to hit Phase A/D quickly.
