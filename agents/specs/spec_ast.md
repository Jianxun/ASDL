# Spec A — Pydantic AST (Schema-Facing) v0 (Revised: named-only conns; add subckt_ref/dummy semantics)

## Purpose
A **loss-minimizing, schema-validated AST** for authoring ASDL in YAML/JSON.
- Validates **shape/types/enums** only.
- Preserves raw strings for expressions/templates.
- Does **not** perform semantic resolution (imports, symbol lookup, ERC, view selection).
- View kinds for v0 are canonical: `{subckt, subckt_ref, primitive, dummy, behav}`. Earlier ADR-0001 reserved-kind sets are superseded by this spec; `behav` is supported for externally evaluated models.

## Conventions
- **Plural nouns** for collections: `imports`, `aliases`, `modules`, `ports`, `views`, `instances`, `templates`, `variables`, `nets`.
- **Named-only binding**: all connections are explicit `port → net` mappings. **Positional connections are forbidden.**

---

## Top-Level: `AsdlDocument`

### Fields
- `doc: Optional[str]`
  - Document docstring for auto-doc generation.
- `top: Optional[str]`
  - Entry module name (prefer fully-qualified, e.g. `"my_lib.top"`).
  - **Not inferred.** If a compilation action needs an entry and `top` is missing, the driver errors.
- `top_mode: Optional[Literal["subckt","flat"]]`
  - Controls presentation of selected top at emission time:
    - `subckt`: emit `.subckt/.ends`
    - `flat`: emit without wrapper (testbench use)
  - Meaningful only when `top` is set.
- `imports: Optional[Dict[str, ImportDecl]]`
  - Namespace imports. Key is the local namespace alias.
- `aliases: Optional[Dict[str, str]]`
  - Optional *pure textual aliases* for module references (e.g. `"n": "std.nmos"`).
  - Expansion rules (v0):
    1. Expanded **before** import/symbol resolution.
    2. **One-step only** (no chaining).
    3. RHS must expand to a qualified module name (or permitted local name).
  - Chaining or unresolved alias RHS is a validation error.
- `modules: Dict[str, ModuleDecl]`
  - Keyed by **qualified module name** (recommended), e.g. `"std.nmos"`.

---

## `ImportDecl`
### Fields
- `from: str`
  - Locator for imported unit (path/URI/package id), uninterpreted in AST.
- `items: Optional[List[str]]`
  - Optional selection list (omit if not supported).

---

## `ModuleDecl`

### Fields
- `doc: Optional[str]`
- `ports: Dict[str, PortDecl]`
- `port_order: List[str]` (mandatory)
- `views: Dict[str, ViewDecl]`
- `metadata: Optional[Dict[str, Any]]`

### Reserved view names
- `nominal` is the canonical default view name.
- `dummy` is reserved for blackout/fallback handling.
- `nom` MAY be accepted as an alias for `nominal` at the importer/linter layer (not required in AST).

(These are naming reserves; they do not by themselves enforce exclusivity.)

---

## `PortDecl`
### Fields
- `dir: Literal["in","out","in_out"]`
- `type: Optional[str]` (default `"signal"`)

---

## `ViewDecl` (discriminated union by `kind`)
Supported kinds (v0):
- `subckt`       — internal structural implementation
- `subckt_ref`   — external structural implementation reference (PEX/external netlist)
- `primitive`    — compiler leaf rendered by backend templates
- `dummy`        — reserved fallback; may be explicitly authored or default-lowered
- `behav`        — externally evaluated behavioral model (VA/ROM/ML surrogate)

### Common fields (all kinds)
- `kind: Literal["subckt","subckt_ref","primitive","dummy","behav"]`
- `doc: Optional[str]`
- `variables: Optional[Dict[str, str]]`  (raw expression strings)
- `metadata: Optional[Dict[str, Any]]`

### `SubcktViewDecl`
- `kind: "subckt"`
- `instances: Optional[Dict[str, InstanceDecl]]`
- `nets: Optional[Dict[str, NetDecl]]`

### `SubcktRefViewDecl`
Represents an externally defined subcircuit implementation (including PEX).
- `kind: "subckt_ref"`
- `ref: SubcktRefDecl`
  - The external handle (include/lib/cell name).
- `pin_map: Optional[Dict[str, str]]`
  - Optional explicit mapping from **module port name → external pin name/index**.
  - If omitted, **identity mapping by port name** is assumed.
  - If the external subckt uses positional pins, `pin_map` **must** be explicit.

### `PrimitiveViewDecl`
- `kind: "primitive"`
- `templates: Dict[str, str]`
  - backend key → template string

### `DummyViewDecl`
- `kind: "dummy"`
- Allowed shapes in v0:
  - **Empty** (no body) → default dummy behavior applied by lowering (backend-defined weak ties).
  - **Exactly one implementation** with:
    - `mode: "weak_gnd"`
    - `params: Optional[Dict[str, Any]]`
- Forbidden in v0:
  - structural instances inside `dummy`
  - templates inside `dummy`
- Author-defined structural/template dummy implementations are deferred to v0.1+.

### `BehavViewDecl`
- `kind: "behav"`
- `model: BehavModelDecl`
- Selection: participates in SelectView like any other view (default `nominal` rules apply). Backend specificity, if any, is handled during lowering, not during selection. Multiple `behav` views may exist if they have distinct names.

---

## `InstanceDecl`
### Fields
- `model: str`
  - Qualified module name or alias.
- `view: Optional[str]`
  - Optional view override in referenced module.
- `conns: Dict[str, str]`  (**named-only; positional forbidden**)
  - Map from **port name → net name**.
- `params: Optional[Dict[str, ParamValue]]`
- `doc: Optional[str]`
- `metadata: Optional[Dict[str, Any]]`

### `ParamValue`
- `int | float | bool | str`
  - Strings may be literals or raw expressions; AST does not interpret.

---

## `NetDecl` (optional)
### Fields
- `type: Optional[str]`
- `doc: Optional[str]`
- `metadata: Optional[Dict[str, Any]]`

---

## `SubcktRefDecl`
External netlist handle (uninterpreted in AST; resolved by tooling/backends).
### Fields (v0 minimal)
- `cell: str`
  - External subckt/cell name to instantiate (often equals module name, but not required).
- `include: Optional[str]`
  - Path/URI for `.include`/library reference.
- `section: Optional[str]`
  - Optional library section/corner identifier.
- `backend: Optional[str]`
  - Optional specificity (e.g. `"lvs.netgen"`, `"sim.spectre"`); if omitted, applies generally.
- `metadata: Optional[Dict[str, Any]]`

---

## `DummyImplDecl` (author-defined dummy behavior; optional)
v0 restriction: **only** `mode: "weak_gnd"` with optional params (e.g. resistance value).
Structural or template-based dummy implementations are deferred to v0.1+.

Parsing/validation do not require `top`; any action that elaborates/netlists/emits **must error** if `top` is not specified.

---

## `BehavModelDecl`
### Fields
- `model_kind: str`   (e.g. `"veriloga"`, `"table"`, `"ml_surrogate"`)
- `ref: str`          (path/URI/registry key)
- `backend: Optional[str]`
- `params: Optional[Dict[str, ParamValue]]`
- `metadata: Optional[Dict[str, Any]]`

---

## Hard Requirements (AST-level)
- `modules` must exist and be a map.
- `ModuleDecl.port_order` must exist.
- `ViewDecl.kind` must be one of supported kinds.
- `InstanceDecl.conns` must be a mapping (named-only).
- `PrimitiveViewDecl.templates` must exist and be a map.

## Deferred to IR verification / passes
- Reference existence & namespace resolution
- Alias expansion validity (one-step, no chaining, qualified RHS)
- Port binding correctness, missing/extra conns
- `dummy` default behavior materialization
- `subckt_ref` include/cell resolution and pin-map validation
- Expression correctness / backend compatibility
