# Task summary (DoD + verify)
- DoD: Expose `file_id` to system-device templates without changing emission behavior. Allow `{file_id}` in `__subckt_header__`, `__subckt_call__`, `__netlist_header__`, and `__netlist_footer__` placeholder validation, plus `{sym_name}` for module templates and `{top_sym_name}` for netlist header/footer. Pass the module's `file_id` into `__subckt_header__`, the referenced module `file_id` into `__subckt_call__`, and the entry `file_id` into netlist header/footer contexts. Implement deterministic subckt renaming for duplicate module names across files using `{sym_name}__{hash8}` (first 8 hex chars of `sha1(file_id)`), applied consistently to `__subckt_header__`, module calls, and `{top}` in netlist header/footer. Add or update emission tests to cover template usage and duplicate-name disambiguation.
- Verify: `pytest tests/unit_tests/emit -v` and `pytest tests/unit_tests/netlist -v`

# Read (paths)
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`

# Plan
- Add/adjust emit/netlist tests for file_id placeholders and duplicate-name hashing.
- Update template placeholder validation + render context to include file_id/sym_name/top_sym_name.
- Implement subckt rename hashing for duplicates across files and apply consistently in headers/calls/top.
- Run emit/netlist unit tests and record results.

## Todo
- [ ] Add tests for file_id placeholder usage + duplicate module name hashing.
- [ ] Update template validation and render context to include file_id/sym_name/top_sym_name.
- [ ] Implement deterministic subckt rename handling for duplicate module names across files.
- [ ] Run emit/netlist tests and capture output.

# Progress log
- 

# Patch summary
- 

# Verification
- 

# Status request (Done / Blocked / In Progress)
- In Progress

# Blockers / Questions
- None.

# Next steps
- 
