# Task summary (DoD + verify)
- DoD: Add registry type aliases for device backend templates and per-expression pattern kinds. Extend RegistrySet with optional fields for these indexes and update exports to keep core registries consistent.
- Verify: None listed.

# Read (paths)
- agents/roles/executor.md
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Todo:
  - [x] Inspect existing registry schemas and exports.
  - [x] Add type aliases and RegistrySet fields per DoD.
  - [x] Update exports and registry serialization for consistency.
  - [ ] Capture progress, commits, and verification notes.

# Progress log

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
- 2026-01-23 19:29 — Task intake and context review; created scratchpad and set T-203 to in_progress; next step inspect registry schema.
- 2026-01-23 19:34 — Updated registry schema aliases and RegistrySet fields; refreshed core exports and patterned graph dump serialization; files touched: src/asdl/core/registries.py, src/asdl/core/__init__.py, src/asdl/core/dump.py; next step commit changes.
