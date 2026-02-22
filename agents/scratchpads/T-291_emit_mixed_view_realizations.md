# Task summary (DoD + verify)
- **DoD**: Update netlist emission naming to support mixed view realizations by deriving emitted module refs from resolved symbols: default -> `cell`, non-default -> `cell_<view>` (sanitized). Preserve deterministic behavior with existing duplicate-name disambiguation and ensure instance calls reference realized emitted names.
- **Verify**: `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/netlist/test_netlist_emitter.py -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `agents/roles/executor.md`

# Plan
- Inspect current netlist render naming path and existing duplicate-name disambiguation behavior.
- Add/adjust tests for mixed-view realization naming and instance call references.
- Implement renderer updates to derive emitted subckt names from resolved module symbols with sanitization.
- Run task verify suite and capture results.

# Milestone notes (optional; brief)
- Intake complete.
- Added test-first coverage for mixed-view module realization names and call refs.
- Implemented realization naming from resolved module symbols in netlist renderer.
- Verify suite passed.

# Patch summary
- Updated module emitted-name derivation in `src/asdl/emit/netlist/render.py`:
  - `cell` and `cell@default` realize to `cell`
  - `cell@view` realizes to `cell_<view>` with sanitization
  - duplicate-name disambiguation now runs on realized names to preserve deterministic uniqueness.
- Added render-level regression in `tests/unit_tests/netlist/test_netlist_render_netlist_ir.py` for default/non-default view realization naming and sanitized output.
- Added emitter-level regression in `tests/unit_tests/netlist/test_netlist_emitter.py` for mixed view symbols plus deterministic hashing on duplicate realized names.

# PR URL
- Pending.

# Verification
- `./venv/bin/pytest tests/unit_tests/netlist/test_netlist_render_netlist_ir.py tests/unit_tests/netlist/test_netlist_emitter.py -v` (pass, 27 tests)

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- None.

# Next steps
- Push branch, open PR, and set task state to `ready_for_review` with PR number.
