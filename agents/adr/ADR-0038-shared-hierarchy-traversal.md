# ADR-0038: Shared Hierarchy Traversal Infrastructure

- Status: Accepted
- Date: 2026-02-25

## Context
Hierarchy traversal is now used by multiple subsystems (`views`, `query`, and
future graph inspection utilities). The codebase currently carries duplicated
traversal logic and module-selection helpers, with one path optimized for
module-only indexing and another path including device leaves.

This duplication creates behavior drift risk:
- inconsistent device inclusion/exclusion
- inconsistent cycle handling and traversal ordering
- repeated bug fixes across subsystems

## Decision
Adopt a shared hierarchy traversal utility as infrastructure.

1. Introduce a canonical traversal module under core infrastructure (target:
   `src/asdl/core/hierarchy.py`).
2. The canonical traversal must expose explicit policy flags, including:
   - inclusion mode for instances (`module_only` vs `module_and_device`)
   - traversal order (`dfs-pre` baseline)
3. `asdl.views.instance_index` must consume shared traversal with
   `module_only` semantics.
4. `asdl.cli.query_runtime` tree payload builders must consume shared traversal
   with `module_and_device` semantics.
5. Module symbol resolution during traversal (name + optional `file_id`) must
   be centralized in the shared utility.

## Consequences
- Positive: one source of truth for hierarchy semantics across views/query.
- Positive: lower maintenance cost and fewer semantic regressions.
- Tradeoff: a small upfront refactor to move working traversal logic into
  shared infrastructure.

## Alternatives
- Keep duplicated traversal logic in each subsystem: rejected due to continued
  drift risk and repeated maintenance overhead.
- Force all subsystems onto one hard-coded traversal mode: rejected because
  views and query intentionally need different inclusion policies.
