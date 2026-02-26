# Spec - Shared Hierarchy Traversal Utility v0

## Purpose
Define a reusable hierarchy traversal contract for NetlistIR designs so
subsystems (`views`, `query`, and future tooling) share one deterministic and
testable traversal behavior.

---

## Scope (v0)
- Canonical traversal over module instances rooted at resolved top.
- Optional inclusion of device instances as leaf nodes.
- Deterministic ordering and cycle policy.
- Shared module-selection behavior by `(file_id, symbol)`.

Out of scope (v0):
- Net-equivalence tracing semantics.
- Mutation/edit operations.
- Performance/caching guarantees.

---

## Data Model

Traversal returns ordered `HierarchyEntry` rows:
- `path: str` (full path including leaf, e.g. `tb.dut.T1`)
- `parent_path: str` (parent path, e.g. `tb.dut`)
- `instance: str` (leaf instance name, e.g. `T1`)
- `ref: str` (referenced symbol)
- `ref_file_id: str` (reference source file id)
- `depth: int` (`path.count(".")`)
- `is_device: bool` (`true` when reference resolves to a device leaf)

---

## API Contract (v0)

Shared utility target:
- `src/asdl/core/hierarchy.py`
- `src/asdl/core/top_resolution.py` (shared top-selection policy helper)

Core entrypoint:
- `traverse_hierarchy(design, *, include_devices, order="dfs-pre") -> list[HierarchyEntry]`
- `resolve_top_module(design) -> NetlistModule | None` (permissive convenience API
  for traversal/query/view callers)

Parameters:
- `include_devices: bool`
  - `False`: include only module-referencing instances.
  - `True`: include module and device instances (devices are leaves).
- `order`: `dfs-pre` only in v0 (reserved for extension).

---

## Semantics

1. Top resolution:
- Top selection must flow through the shared policy helper in
  `src/asdl/core/top_resolution.py`.
- Traversal/query/views use permissive policy:
  - `design.top` + optional `entry_file_id` exact match preferred
  - when `design.top` is absent, infer only for a unique entry-file module or
    unique global module
  - ambiguous/missing top resolves to `None` (non-fatal at this layer)

2. Traversal:
- Walk instances in authored module instance order.
- Use DFS preorder from top.
- For each instance, emit one `HierarchyEntry`.

3. Module recursion:
- Recurse only when instance reference resolves to a module symbol.
- Device references are always leaves.

4. Cycle policy:
- Track module ancestry by `(file_id, module_name)`.
- If next target already exists in ancestry, emit current entry and stop
  recursion at that edge.

5. Symbol resolution:
- Resolve module target by exact `(file_id, name)` when `file_id` is present.
- If `file_id` is absent, use deterministic name-only fallback:
  - unique candidate by name -> select that candidate
  - multiple candidates by name -> select last deterministic candidate

---

## Reuse Requirements

- `asdl.views.instance_index` must call shared traversal with
  `include_devices=False`.
- `asdl.cli.query_runtime` tree payload builders must call shared traversal
  with `include_devices=True`.
- Subsystems must not duplicate module-selection helpers once migrated.
- Subsystems must not duplicate top-resolution semantics once migrated; both
  traversal and emission-facing code paths must consume the shared top policy
  helper with caller-appropriate strictness.

---

## Determinism

For fixed design inputs:
- row ordering is deterministic
- parent/child path derivation is deterministic
- fallback module selection is deterministic

---

## References
- ADR: `agents/adr/ADR-0038-shared-hierarchy-traversal.md`
- ADR: `agents/adr/ADR-0039-shared-top-resolution-policy.md` (Proposed)
- Query semantics: `docs/specs/spec_cli_query.md`
- View semantics: `docs/specs/spec_asdl_view_config.md`
