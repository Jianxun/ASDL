# T-020 — Core IR Dialect Rename (ASDL_CIR)

## Task summary
- DoD: Rename core xDSL dialect to `asdl_cir` in code/tests; update converter usage and IR text expectations to match ASDL_CIR naming; keep semantics unchanged.
- Verify: `pytest tests/unit_tests/ir`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `agents/context/codebase_map.md`
- `agents/scratchpads/T-020_cir_rename.md`
- `src/asdl/ir/xdsl_dialect/asdl_cir.py`
- `src/asdl/ir/xdsl_dialect/__init__.py`
- `src/asdl/ir/__init__.py`
- `src/asdl/ir/converter.py`
- `tests/unit_tests/ir/test_converter.py`
- `tests/unit_tests/ir/test_dialect.py`
- `src/asdl/__init__.py`

## Plan
1. Restore IR dialect and converter sources from T-012 branch to serve as rename baseline.
2. Rename dialect/ops/attrs to `asdl_cir` and update module exports.
3. Update map/docs that describe active refactor surface to include IR.
4. Run IR unit tests.
5. Update handoff/tasks/scratchpad status.

## Progress log
- Restored IR sources/tests from `feature/T-012-ir-dialect` into this branch.
- Renamed `asdl` dialect/op/attr names to `asdl_cir`, including file rename to `asdl_cir.py`.
- Updated exports to include `ASDL_CIR` (with `ASDL` alias).
- Updated `agents/context/codebase_map.md` and `src/asdl/__init__.py` to reflect active IR surface.

## Patch summary
- `src/asdl/ir/xdsl_dialect/asdl_cir.py`: rename dialect/op/attr names to `asdl_cir`; add `ASDL_CIR` alias.
- `src/asdl/ir/xdsl_dialect/__init__.py`: import from `asdl_cir`, export `ASDL_CIR`.
- `src/asdl/ir/__init__.py`: export `ASDL_CIR`.
- `src/asdl/ir/converter.py`: restored from T-012 baseline.
- `tests/unit_tests/ir/test_converter.py`: restored from T-012 baseline.
- `tests/unit_tests/ir/test_dialect.py`: restored from T-012 baseline.
- `agents/context/codebase_map.md`: reflect `src/asdl/ir` and remove deleted legacy editor extension entry.
- `src/asdl/__init__.py`: update active refactor surface note.

## PR URL
- https://github.com/Jianxun/ASDL/pull/24

## Verification
- `./venv/bin/python -m pytest tests/unit_tests/ir` (passed).

## Blockers / Questions
- None.

## Next steps
1. Run `pytest tests/unit_tests/ir`.
2. Update handoff/tasks with results.
