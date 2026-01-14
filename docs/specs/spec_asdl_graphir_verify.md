# ASDL GraphIR Verification Specification

Status: Draft

## 1. Purpose

This document defines the verification rules that run on GraphIR, the canonical
semantic core. GraphIR verification must succeed before downstream projections
to IFIR and emission.

## 2. Pre-GraphIR Preconditions

These checks run before GraphIR construction:
- AST schema validation (required fields, list shapes, token presence).
- Import resolution and symbol identity (`file_id`, `(file_id, name)`).
- Pattern expansion and length computation (metadata only; no inference).
- Token-level validation (instance expr tokens, endpoint token syntax).

## 3. GraphIR Invariants

### 3.1 Structural Invariants (all modules)

- Every instance reference resolves to a module or device symbol.
- Instance names are unique within a module.
- Net names are unique within a module.
- Endpoint key uniqueness: `(inst_id, port_path)` appears at most once.
- Each endpoint attaches to exactly one net.
- All endpoints reference valid instances.
- All nets and instances exist.
- Endpoint IDs are unique within a module.
- If `graphir.program.entry` is set, it must refer to a module symbol.

### 3.2 Port and Interface Consistency

- For module symbols:
  - Port names are unique within `graphir.module.attrs.port_order`.
  - Every endpoint `port_path` must match a declared port name.
- For device symbols:
  - If `ports` is non-empty, every endpoint must match a device port.
  - If `ports` is empty, port-name checking is skipped (portless device).
- Port names and endpoint `port_path` must not contain `.`; `inst.port` is the
  only endpoint expression form in scope for MVP.

### 3.3 Pattern/Bundling Consistency

- Pattern metadata is present only on expander-produced atoms.
- Bundle members are ordered lists; order must match expander output.
- Bundle members must exist and be compatible with `kind`.
- Pattern expressions list bundles of the same `kind` in order.
- Each bundle belongs to at most one pattern expression per kind.
- `pattern_expr.owner` must exist and match `kind` (net/endpoint/param/inst).
- At most one pattern expression is allowed per `owner` and `kind`.
- No pattern inference is performed during verification.

### 3.4 Binding and Expansion Semantics

Binding is verified using the expanded atom order:
- If a net expands to length `N > 1`, every bound endpoint must expand to `N`.
- If a net is scalar (`N == 1`), it may bind to endpoints of any length; each
  expanded endpoint atom binds to the single net.
- Scalar endpoints bind to exactly one net.
- Expansion length limits must not exceed configured cap (default 10k).

## 4. Ordering and Determinism

- GraphIR preserves expander order for all pattern bundles.
- Rebundling uses member list order; verification never reorders members.
- Module emission order is computed outside verification (see GraphIR spec).

## 5. Diagnostics

Verification failures must emit structured diagnostics with:
- code, severity, message, and source span (when available)
- related labels for the involved endpoints/nets/instances
- optional fix-it suggestions for common violations

## 6. Out of Scope

The following are not GraphIR verification responsibilities:
- AST tokenization and parsing errors
- Import resolution conflicts and cycle errors
- Backend template validation and system device requirements
- Emission formatting rules and backend-specific constraints
