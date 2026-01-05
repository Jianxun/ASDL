# T-053 Pattern Expansion

## Task summary
- DoD: Preserve raw pattern tokens verbatim in AST/NFIR/IFIR (no basename+pattern decomposition). Update parsers/converters to retain the original token strings; add tests to ensure round-trip preservation through NFIR/IFIR.
- Verify: `pytest tests/unit_tests/ast -v`, `pytest tests/unit_tests/ir -v`

## Read
- `agents/roles/executor.md`
- `agents/context/lessons.md`
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `docs/specs/spec_asdl_pattern_expansion.md`
- `src/asdl/ast/models.py`
- `src/asdl/ast/parser.py`
- `src/asdl/ir/converters/ast_to_nfir.py`
- `src/asdl/ir/converters/nfir_to_ifir.py`
- `src/asdl/ir/nfir/dialect.py`
- `src/asdl/ir/ifir/dialect.py`
- `tests/unit_tests/parser/test_parser.py`
- `tests/unit_tests/ir/test_converter.py`
- `tests/unit_tests/ir/test_ifir_converter.py`

## Plan
1. Add parser coverage that loads pattern tokens in instance/net/endpoint slots.
2. Add AST->NFIR test to assert pattern tokens survive into NFIR attributes.
3. Add NFIR->IFIR test to assert pattern tokens survive in IFIR attributes.
4. Run targeted AST/IR tests.

## Progress log
- Created feature branch `feature/T-053-pattern-expansion`.
- Marked T-053 as `in_progress` in `agents/context/tasks_state.yaml`.
- Added parser/IR tests covering pattern token preservation.
- Ran parser/AST/IR unit tests.

## Patch summary
- `agents/context/tasks_state.yaml`: set T-053 to `in_progress`.
- `tests/unit_tests/parser/test_parser.py`: added parser round-trip test for pattern tokens.
- `tests/unit_tests/ir/test_converter.py`: added AST->NFIR preservation test.
- `tests/unit_tests/ir/test_ifir_converter.py`: added NFIR->IFIR preservation test.

## Verification
- `venv/bin/pytest tests/unit_tests/parser -v`
- `venv/bin/pytest tests/unit_tests/ast -v`
- `venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Ready for Review

## Blockers / Questions
- None.

## Next steps
1. Push branch and open PR for T-053.
