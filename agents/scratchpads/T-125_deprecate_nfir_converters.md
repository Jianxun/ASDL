# Task summary (DoD + verify)
- DoD: Hard-deprecate AST->NFIR and NFIR->IFIR converters by removing them from public exports, relocating the modules under `legacy/` (or deleting them if no longer needed), and updating any call sites to use AST->GraphIR and GraphIR->IFIR instead. Update/trim tests to match the new export surface, and document NFIR as projection-only.
- Verify: `venv/bin/pytest tests/unit_tests/ir -v`

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Explain task understanding and confirm scope (exports, relocations, call sites, tests, doc note).
- Update call sites/tests to the GraphIR pipeline and adjust public exports.
- Relocate or remove NFIR converters under legacy and update docs.
- Verify and record results.

# Todo
- [ ] Review current NFIR converter exports/usages and decide deletions vs legacy moves.
- [ ] Update tests/imports to use AST->GraphIR + GraphIR->IFIR only.
- [ ] Remove NFIR converters from public exports.
- [ ] Relocate NFIR converter modules under legacy/ (or delete).
- [ ] Document NFIR as projection-only in spec.

# Progress log
- 2026-01-14: Understanding: remove AST->NFIR and NFIR->IFIR from public exports, move converter modules to legacy (or delete), update tests/call sites to GraphIR path, and document NFIR as projection-only.

# Patch summary

# PR URL

# Verification

# Status request (Done / Blocked / In Progress)

# Blockers / Questions

# Next steps
