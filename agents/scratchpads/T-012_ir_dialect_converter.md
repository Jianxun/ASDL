# T-012 — xDSL Dialect + AST→IR

## Task summary
- DoD: Implement xDSL `asdl.ir` dialect ops/attrs per `docs/specs/spec_asdl_ir.md` with verifiers; update AST→IR converter to emit `asdl.design/module/view/...` and enforce canonical `nominal` during emission; add unit tests (skip if xdsl optional dep missing).
- Verify: `pytest tests/unit_tests/ir`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.md`
- `agents/context/handoff.md`
- `docs/specs/spec_ast.md`
- `docs/specs/spec_asdl_ir.md`

## Plan
1. Inspect current `src/asdl/ir` layout and existing converter/dialect stubs.
2. Implement `asdl.ir` dialect ops/attrs + verifiers per spec.
3. Update AST→IR converter, including `nom` → `nominal` normalization.
4. Add/adjust unit tests with optional xdsl dependency skip.
5. Run `pytest tests/unit_tests/ir`.

## Progress log
- Read spec AST/IR docs and executor instructions; task marked In Progress.
- Implemented `asdl.ir` dialect ops/attrs, verifier rules, and AST→IR converter with view normalization.
- Added IR unit tests and confirmed they pass.

## Patch summary
- Added new `src/asdl/ir` package with xDSL dialect definitions and converter.
- Added IR unit tests under `tests/unit_tests/ir`.
- Updated `agents/context/codebase_map.md` to reflect new IR package.

## Verification
- `venv/bin/python -m pytest tests/unit_tests/ir`

## Blockers / Questions
- None yet.

## Next steps
1. Push branch `feature/T-012-ir-dialect` and open PR referencing T-012 + scratchpad.
2. Await review/approval.
