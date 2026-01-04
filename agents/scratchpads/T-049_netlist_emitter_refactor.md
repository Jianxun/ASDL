# T-049 Netlist Emitter Refactor

## Task summary
- DoD: Refactor `src/asdl/emit/netlist.py` into a package with clear separation of validation vs rendering. Create `src/asdl/emit/netlist/` modules: `__init__.py` (re-exports), `api.py` (emit_netlist/load_backend orchestration), `verify.py` (VerifyNetlistPass + verification runner), `render.py` (emit_design/module/instance + system device rendering), `templates.py` (placeholder parsing/validation + system-device placeholder rules/constants), `params.py` (param merge + attr stringify helpers), `ir_utils.py` (collect ops, resolve top, find single design), `diagnostics.py` (diagnostic codes + helpers). Preserve public API: `from asdl.emit.netlist import EmitOptions, VerifyNetlistPass, emit_netlist, load_backend` remains valid via re-exports. Ensure no behavior changes (byte-for-byte netlist output + diagnostics) beyond necessary import paths. Update imports across `src/asdl/emit/`, `src/asdl/cli/`, and tests as needed. Add/adjust any internal imports to avoid cycles. Update `agents/context/codebase_map.md` emission section to reflect new netlist package layout.
- Verify: `pytest tests/unit_tests/emit -v && pytest tests/unit_tests/netlist -v && pytest tests/unit_tests/cli -v && pytest tests/unit_tests/e2e -v`

## Read
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `src/asdl/emit/netlist.py`
- `src/asdl/emit/__init__.py`
- `agents/context/codebase_map.md`

## Plan
- Inspect `src/asdl/emit/netlist.py` and related emitter/cli/test imports.
- Split code into the specified modules, preserving behavior and public API via re-exports.
- Update imports and codebase map; avoid cycles.
- Run verification commands or note if not run.

## Progress log
- Initialized scratchpad and read context files.
- Split netlist emitter into package modules and updated codebase map.
- Ran emit/netlist/cli/e2e test suites.

## Patch summary
- `src/asdl/emit/netlist/__init__.py`: re-export netlist public API.
- `src/asdl/emit/netlist/api.py`: emit/load orchestration with EmitOptions.
- `src/asdl/emit/netlist/verify.py`: verification pass and runner.
- `src/asdl/emit/netlist/render.py`: design/module/instance emission and system device rendering.
- `src/asdl/emit/netlist/templates.py`: placeholder parsing and template validation rules.
- `src/asdl/emit/netlist/params.py`: param merging and attr stringification helpers.
- `src/asdl/emit/netlist/ir_utils.py`: design/module/device discovery helpers.
- `src/asdl/emit/netlist/diagnostics.py`: diagnostic codes and helpers.
- `src/asdl/emit/netlist.py`: removed (replaced by package).
- `agents/context/codebase_map.md`: updated emitter layout.

## Verification
- `venv/bin/python -m py_compile src/asdl/emit/netlist/*.py`
- `venv/bin/pytest tests/unit_tests/emit -v`
- `venv/bin/pytest tests/unit_tests/netlist -v`
- `venv/bin/pytest tests/unit_tests/cli -v`
- `venv/bin/pytest tests/unit_tests/e2e -v`

## Blockers / Questions
- User requested no new feature branch; this deviates from executor role guidance. Proceeding on current branch unless instructed otherwise.

## Next steps
- Inspect current netlist emitter module and call sites.
