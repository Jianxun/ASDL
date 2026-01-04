# T-054 Imports/Dependency Spec

## Context
Multi-file import support and dependency management are not specified yet. We need a formal spec before implementation.

## Notes
- Define syntax (file-level import declarations), resolution rules, cycle handling, and diagnostics.
- Decide where imports are resolved in the pipeline and how source spans are tracked.
- Document migration from MVP single-file flow.

## DoD
- New spec doc under `docs/specs/` covering imports/deps.
- Pipeline boundaries clarified, including diagnostics expectations.
- Open questions and non-goals documented.
