# Spec B — ASDL_CIR (xDSL Dialect `asdl_cir`) v0 (Revised: named-only conns; add subckt_ref/dummy/behav; SelectView contract)

## Purpose
IR ID: **ASDL_CIR** (formerly `asdl.ir`).
A compiler-facing structural IR that:
- normalizes connectivity into explicit named edges,
- supports deterministic name resolution and ERC-like verifications,
- preserves raw strings for templates/expressions,
- remains backend-agnostic; backends are chosen in later lowering passes.
- View kinds for v0 are canonical: `{subckt, subckt_ref, primitive, dummy, behav}`. Earlier ADR-0001 reserved-kind sets are superseded by this spec; `behav` is supported for externally evaluated models.

---

## 1) Symbols and Containment

### Symbols
- `asdl_cir.module` is a symbol addressable by name (qualified string allowed).
- `asdl_cir.view` is a nested symbol within `asdl_cir.module`.

### Symbol Tables
- `asdl_cir.design` owns a symbol table of `asdl_cir.module`.
- `asdl_cir.module` owns a symbol table of its `asdl_cir.view`.

---

## 2) Ops

### 2.1 `asdl_cir.design`
**Role**: top-level compilation unit container.

**Attributes**
- `doc: StringAttr?`
- `top: StringAttr?` (or SymbolRefAttr once linked)
- `top_mode: StringAttr?` ∈ {`"subckt"`, `"flat"`}
- `unit_name: StringAttr?`
- `src: LocAttr?`

**Region**
- contains: `asdl_cir.import*`, `asdl_cir.module*`

**Verifier (v0)**
- module symbol names unique.

---

### 2.2 `asdl_cir.import`
**Attributes**
- `as_name: StringAttr`
- `from: StringAttr`
- `items: ArrayAttr<StringAttr>?`
- `src: LocAttr?`

**Verifier**
- no duplicate `as_name` within a design.

---

### 2.3 `asdl_cir.module` (symbol)
**Attributes**
- `sym_name: StringAttr`
- `doc: StringAttr?`
- `port_order: ArrayAttr<StringAttr>` (mandatory)
- `src: LocAttr?`

**Region**
- contains: `asdl_cir.port*`, `asdl_cir.view*`

**Verifier**
- port names unique
- `port_order` matches declared ports (permutation)

---

### 2.4 `asdl_cir.port`
**Attributes**
- `name: StringAttr`
- `dir: StringAttr`
- `type: StringAttr`
- `src: LocAttr?`

**Verifier**
- `dir` ∈ {`"in"`, `"out"`, `"in_out"`}

---

### 2.5 `asdl_cir.view` (nested symbol)
Supported `kind` (v0):
- `subckt`       — internal structural implementation
- `subckt_ref`   — external structural implementation reference
- `primitive`    — compiler leaf via templates
- `dummy`        — reserved fallback; explicit or default-lowered
- `behav`        — externally evaluated behavioral model

**Attributes**
- `sym_name: StringAttr`
- `kind: StringAttr`
- `doc: StringAttr?`
- `src: LocAttr?`

**Region**
- Common: `asdl_cir.var*` (optional)
- `kind=subckt`: `asdl_cir.net*` (optional), `asdl_cir.instance*`
- `kind=primitive`: `asdl_cir.template*`
- `kind=subckt_ref`: exactly one `asdl_cir.subckt_ref`
- `kind=dummy`: `asdl_cir.dummy_mode?`
- `kind=behav`: exactly one `asdl_cir.behav_model`

**Verifier (v0)**
- `primitive`: ≥1 template; no instances
- `subckt_ref`: exactly one `asdl_cir.subckt_ref`; no instances/templates
- `behav`: exactly one `asdl_cir.behav_model`; no instances/templates
- `dummy`: allowed forms:
  - any number of `asdl_cir.var*`
  - zero or one `asdl_cir.dummy_mode`
  - forbidden: `asdl_cir.instance`, `asdl_cir.template`, `asdl_cir.behav_model`, `asdl_cir.subckt_ref`
- coupling rule (v0):
  - if `kind=="dummy"`, then `sym_name` MUST be `"dummy"`
  - no other view kind may use the name `"dummy"`

**Dummy default semantics**
- Default dummy semantics apply when no `asdl_cir.dummy_mode` is present, regardless of `asdl_cir.var*`.

---

### 2.6 `asdl_cir.net` (optional)
**Attributes**
- `name: StringAttr`
- `net_type: StringAttr?`
- `implicit: BoolAttr?`
- `src: LocAttr?`

**Verifier**
- unique net names per view.

---

### 2.7 `asdl_cir.instance`
**Role**: structural instance statement with **named-only** connectivity.

**Attributes**
- `name: StringAttr`
- `ref: SymbolRefAttr` (module reference; may be unresolved pre-link)
- `view: StringAttr?` (optional override)
- `params: DictAttr?`
- `conns: ArrayAttr<asdl_cir.conn>`  (**named-only**)
- `doc: StringAttr?`
- `src: LocAttr?`

**Verifier (v0)**
- instance names unique within a view
- ports unique within `conns`
- (**invariant**) IR MUST NOT contain positional connection forms

---

### 2.8 `asdl_cir.template`
**Attributes**
- `backend: StringAttr`
- `text: StringAttr`
- `src: LocAttr?`

---

### 2.9 `asdl_cir.var`
**Attributes**
- `name: StringAttr`
- `expr: asdl_cir.expr`
- `src: LocAttr?`

---

### 2.10 `asdl_cir.subckt_ref`
**Role**: external structural implementation handle.

**Attributes**
- `cell: StringAttr`          (external subckt/cell name)
- `include: StringAttr?`      (path/URI)
- `section: StringAttr?`      (corner/section)
- `backend: StringAttr?`      (optional specificity)
- `pin_map: DictAttr?`        (module_port → external_pin token)
- `src: LocAttr?`

**Verifier (v0)**
- `cell` non-empty
- If `pin_map` absent: identity mapping (module port → same-named external pin) is assumed.
- If `pin_map` present:
  - keys must exactly match the module’s port set (v0 rule)
  - values are external pin tokens; external validation occurs post-link/backend

---

### 2.11 `asdl_cir.behav_model`
**Attributes**
- `backend: StringAttr?`
- `model_kind: StringAttr`
- `ref: StringAttr`
- `params: DictAttr?`
- `src: LocAttr?`

---

### 2.12 `asdl_cir.dummy_mode` (optional helper op)
**Role**: explicit dummy semantics without authoring full topology.

**Attributes**
- `mode: StringAttr` (v0: `"weak_gnd"`)
- `params: DictAttr?` (e.g. `{r: "1e9"}` as ExprStr)
- `src: LocAttr?`

---

## 3) Dialect Attributes

### 3.1 `asdl_cir.conn` (Attr)
- `port: StringAttr`
- `net: StringAttr`

### 3.2 `asdl_cir.expr` (Attr)
- `text: StringAttr` (raw expression string)

---

## 4) Compiler Pass Contracts (Required Semantics)

### 4.1 Link/Resolve Pass
- resolves `SymbolRefAttr` references using:
  - `asdl_cir.import` namespace bindings
  - module/view symbol tables
  - `aliases` expansion (if supported) before resolution
- alias rules (v0):
  - pure textual substitution
  - one-step only (no chaining)
  - RHS must resolve to a qualified module name (or permitted local)
  - chaining or unresolved RHS is an error
- validates reserved view names handling (see SelectView)

### 4.2 Verify/ERC Passes (non-exhaustive)
- instance port binding correctness:
  - every required port bound exactly once (unless allowed otherwise)
  - no unknown port names
- net/port naming collision policies
- `subckt_ref.pin_map` validity against module ports (keys) and external pins (tokens)

### 4.3 SelectView Pass (semantic contract)
- validates **all views** (no deferred validation)
- produces a resolved `(instance → selected_view)` mapping for downstream passes
- default view selection:
  - if instance specifies `view`: use it
  - else select `nominal`
  - else error (if no nominal exists and no override provided)
- `dummy` view name and kind are strictly coupled (see `asdl_cir.view` verifier)
- `behav` views participate like any other view; backend specificity is handled during lowering, not selection

(IR operates on canonical `nominal` only; `nom` alias normalization must occur before IR emission.)
(Exact “view_order/config overlay” mechanics are outside `asdl_cir` v0 but the pass exists as an architectural boundary.)

### 4.4 Lowering/Emission Passes
- choose backend templates or external refs
- implement `top/top_mode`:
  - error if an entry point is required and `top` missing
  - `subckt`: wrap selected top as `.subckt/.ends`
  - `flat`: emit without wrapper
- implement default dummy behavior when no `asdl_cir.dummy_mode` is present:
  - default weak ties to GND via backend-specific primitive expansion when no `asdl_cir.dummy_mode` is present
  - if dummy explicitly authored via `asdl_cir.dummy_mode`, respect author intent
- Parsing/IR construction do not require `top`; any action that elaborates/netlists/emits **must error** if `top` is not specified.

---

## 5) Invariants
- IR connectivity is **named-only** (`asdl_cir.conn` list). No positional binding exists in IR.
- `port_order` is mandatory and canonical for modules (even though conns are named-only).
- Backend quirks are localized to lowering/templates, not to `asdl_cir` semantics.
