# Spec - NetlistIR (Emission-Ready Dataclass IR) v0

## Purpose
Define the dataclass-based NetlistIR model used as the emission-ready
representation in the refactor pipeline. NetlistIR replaces IFIR as the
normalized input to backend netlist emission and verification.

---

## Scope (v0)
- Multi-file designs are supported; symbol identity is `(file_id, name)`.
- Named-only connections (no positional conns).
- Explicit net objects are declared per module.
- Pattern tokens are expanded before NetlistIR; NetlistIR names are literal.
- Optional structured `pattern_origin` metadata preserves provenance; modules
  may carry a `pattern_expression_table` keyed by expression IDs.
- Backend templates are attached to devices for emission (system devices remain
  defined in backend config).

---

## Dataclass model

```python
@dataclass(frozen=True)
class NetlistDesign:
    modules: list[NetlistModule]
    devices: list[NetlistDevice]
    top: str | None
    entry_file_id: str | None

@dataclass(frozen=True)
class NetlistModule:
    name: str
    file_id: str
    ports: list[str]
    nets: list[NetlistNet]
    instances: list[NetlistInstance]
    pattern_expression_table: dict[str, PatternExpressionEntry] | None = None

@dataclass(frozen=True)
class NetlistNet:
    name: str
    net_type: str | None = None
    pattern_origin: PatternOrigin | None = None

@dataclass(frozen=True)
class NetlistInstance:
    name: str
    ref: str
    ref_file_id: str
    params: dict[str, str] | None
    conns: list[NetlistConn]
    pattern_origin: PatternOrigin | None = None

@dataclass(frozen=True)
class NetlistConn:
    port: str
    net: str

@dataclass(frozen=True)
class NetlistDevice:
    name: str
    file_id: str
    ports: list[str]
    params: dict[str, str] | None
    variables: dict[str, str] | None
    backends: list[NetlistBackend]

@dataclass(frozen=True)
class NetlistBackend:
    name: str
    template: str
    params: dict[str, str] | None
    variables: dict[str, str] | None
    props: dict[str, str] | None

@dataclass(frozen=True)
class PatternOrigin:
    expression_id: str
    segment_index: int
    base_name: str
    pattern_parts: list[str | int]

@dataclass(frozen=True)
class PatternExpressionEntry:
    expression: str
    kind: Literal["net", "inst", "endpoint", "param"]
    span: SourceSpan | None = None
```

Notes:
- Lists preserve deterministic order; emitters should preserve module/net/
  instance ordering as provided.
- Dictionaries in NetlistIR store literal string values; upstream lowering
  determines the exact formatting. Emitters must treat these as raw strings.
- Optional `pattern_origin` is provenance-only; identity uses literal names.

---

## Pattern provenance (design)

`pattern_origin` is optional metadata attached to atomized names:

```
PatternOrigin {
  expression_id: str
  segment_index: int
  base_name: str
  pattern_parts: list[str | int]
}
```

Rules:
- `expression_id` refers to a module-local entry in `pattern_expression_table`.
- `segment_index` counts `;`-separated segments in the original expression.
- `pattern_origin` does not affect identity; it is used for provenance and
  presentation (e.g., backend numeric formatting).

`pattern_expression_table` maps `expression_id` to:

```
PatternExpressionEntry {
  expression: str
  kind: net | inst | endpoint | param
  span?: SourceSpan
}
```

### What is preserved
- Expression identity: `expression_id` is stable within a module and can be
  shared by multiple nets/instances/endpoints derived from the same authored
  pattern.
- Segment/atom addressing: `segment_index` and the implicit atom index encode
  which splice segment and atom in the expansion produced the literal.
- Base name + parts: `base_name` plus `pattern_parts` allow reconstructing a
  human-readable patterned name without re-expanding the full expression.
- Source span: optional span in the expression table supports diagnostics that
  point to the authored pattern.

### What is intentionally *not* preserved
- Pattern expansion semantics: NetlistIR never infers or re-expands patterns;
  identity remains the literal name.
- Non-local reconstruction: no cross-module provenance or global registry is
  required; provenance is strictly module-local.
- Connectivity semantics: provenance does not affect net/instance connectivity.

### Intended uses
- Diagnostics provenance: report invalid pattern origins or missing expression
  entries with stable IDs and optional spans.
- Presentation formatting: emitters may display names using base + parts with
  backend-specific numeric formatting rules, falling back to the literal if
  provenance is missing/invalid.
- Tooling/debugging: visualization and inspection tools can show pattern
  structure without bundling atoms back into expressions.

---

## Derivation (AtomizedGraph -> NetlistIR)
- Top selection:
  - If an explicit top module id is supplied, use that module.
  - Else if only one module exists, use it as top.
- For each module:
  - copy `name`, `file_id`, `ports`.
  - build `NetlistNet` entries from atomized nets.
  - invert atomized endpoints into instance `conns` (named-only).
  - copy `pattern_origin` metadata when registries exist.
  - build `pattern_expression_table` from referenced expression ids when
    registries exist.
- For each device:
  - copy `name`, `file_id`, `ports`, `parameters`, `variables`.
  - attach backend templates and backend metadata from registries.

---

## Verification (stateless)
NetlistIR verification is performed by pure functions that return diagnostics
without mutating inputs. Verification should be gated by prior stages when
appropriate (e.g., only run if AtomizedGraph verification is clean).

Required checks (v0):
- All net and instance names are literal; pattern delimiters are forbidden.
- Net names are unique within a module.
- Instance names are unique within a module.
- Each instance's conns list has unique `port` names.
- Each conn.net refers to a declared net in the same module.
- `ports` is a list of unique names, and each entry corresponds to a net.
- Device backend names are unique per device.
- If any net or instance carries `pattern_origin`, the module must provide
  `pattern_expression_table`, and each referenced `expression_id` must exist
  with matching `kind`.

Optional deep checks (when pattern expressions are available):
- Validate that `pattern_origin` indices and literals are consistent with the
  referenced expression's expansion (segment and atom indices).

Diagnostics:
- Emit diagnostics via the centralized catalog in
  `docs/specs/spec_diagnostic_codes.md`. Each rule should map to a stable IR
  code with source `ir` or `core` (see NetlistIR verifier policy).

---

## Invariants
- Module names are unique per `file_id`.
- Device names are unique per `file_id`.
- Net names are unique within a module.
- Instance names are unique within a module.
- Each instance's conns list has unique `port` names.
- Each conn.net refers to a declared net in the same module.
- `ports` is a list of unique names, and each entry corresponds to a net.
- Backend `name` keys are unique per device.
- `pattern_origin` does not affect identity; it is provenance-only.
