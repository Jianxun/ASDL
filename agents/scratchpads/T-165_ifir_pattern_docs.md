# Task summary (DoD + verify)
- DoD: Update IFIR and netlist emission specs to describe structured pattern_origin metadata, the pattern expression table, and the emitter's use of pattern provenance for presentation formatting.
- Verify: rg -n "pattern_origin" docs/specs/spec_asdl_ifir.md docs/specs/spec_netlist_emission.md

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md

# Plan
- Review current IFIR and netlist emission specs for pattern provenance context.
- Update specs to describe structured pattern_origin metadata and pattern expression table.
- Document emitter usage of pattern provenance for formatting.
- Verify required strings appear and update scratchpad.

# Todo
- [x] Update `spec_asdl_ifir.md` with structured pattern provenance/table details.
- [x] Update `spec_netlist_emission.md` for emitter formatting behavior.

# Progress log
- 2026-xx-xx: Created scratchpad and loaded task context.
- 2026-xx-xx: Understanding: document IFIR pattern provenance schema/table and netlist emission formatting use.
- 2026-xx-xx: Documented IFIR pattern provenance metadata/table in spec.
- 2026-xx-xx: Documented netlist emission formatting rules for pattern provenance.
- 2026-xx-xx: Opened PR #167.

# Patch summary
- Documented structured `pattern_origin` metadata and the module-level pattern
  expression table in the IFIR spec.
- Added netlist emission guidance for formatting names with pattern provenance.

# PR URL
- https://github.com/Jianxun/ASDL/pull/167

# Verification
- `rg -n "pattern_origin" docs/specs/spec_asdl_ifir.md docs/specs/spec_netlist_emission.md`

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions

# Next steps
- Await review.
