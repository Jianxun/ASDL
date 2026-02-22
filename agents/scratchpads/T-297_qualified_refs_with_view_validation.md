# T-297 - Restore import-qualified instance refs with decorated-symbol validation

## Task summary (DoD + verify)
- Fix AST instance-ref validation so import-qualified refs (`ns.symbol`) are accepted while preserving decorated view grammar checks (`cell` or `cell@view`) on symbol tokens.
- Keep module declaration-name validation strict (`cell`/`cell@view` only).
- Preserve specific parser diagnostics for malformed `@` usage.
- Add self-contained regressions for valid qualified refs and malformed decorated variants.
- Verify with:
  - `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/parser/test_parser.py tests/unit_tests/cli/test_netlist.py -k "imports_with or malformed_decorated or module_symbol or qualified" -v`

## Read (paths)
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/ast/models.py`
- `tests/unit_tests/ast/test_models.py`
- `tests/unit_tests/parser/test_parser.py`
- `tests/unit_tests/cli/test_netlist.py`

## Plan
1. Mark task `in_progress`, lint task state, and create feature branch from `main`.
2. Add failing regressions for `ns.symbol` / `ns.symbol@view` plus malformed decorated qualified refs.
3. Split instance-ref validation from module-symbol declaration validation in AST models.
4. Re-run task verify command and resolve regressions.
5. Close out scratchpad/task state and hand off for review.

## Milestone notes
- Added regression coverage first; confirmed failures reproduced for qualified refs.
- Implemented `InstanceRef` validation path for instance refs while keeping `ModuleSymbol` unchanged for declarations.
- Verified parser/CLI now accept qualified refs, including decorated symbol refs (`ns.symbol@view`).

## Patch summary
- `src/asdl/ast/models.py`
  - Added `_validate_instance_ref` for `symbol` and `ns.symbol` forms.
  - Added `InstanceRef` type alias and applied it to `InstanceDecl.ref`.
  - Updated inline instance-ref validator to use `_validate_instance_ref`.
  - Preserved decorated symbol grammar checks via `_validate_module_symbol(symbol)`.
- `tests/unit_tests/ast/test_models.py`
  - Added coverage for valid qualified structured/inline refs.
  - Added malformed qualified decorated variants.
- `tests/unit_tests/parser/test_parser.py`
  - Added parser acceptance test for `ns.symbol` and `ns.symbol@view`.
  - Added parser diagnostic checks for malformed qualified decorated refs.
- `tests/unit_tests/cli/test_netlist.py`
  - Added self-contained import fixture with decorated module symbol.
  - Added CLI regression for `lib.leaf@behave` emission path.

## PR URL
- Pending PR creation.

## Verification
- `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/parser/test_parser.py tests/unit_tests/cli/test_netlist.py -k "imports_with or malformed_decorated or module_symbol or qualified" -v`
  - Result: 23 passed, 68 deselected.

## Status request
- Ready for review after PR creation.

## Blockers / Questions
- None.

## Next steps
- Push branch and open PR to `main`.
- Update `agents/context/tasks_state.yaml` to `ready_for_review` with PR number and `merged: false`.
