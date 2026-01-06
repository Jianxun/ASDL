# T-058 Pattern Binding Verification

## Task summary
- DoD: Implement pattern binding verification for nets/endpoints (total length comparison, scalar net broadcast, patterned net requires all endpoint lengths match). Emit diagnostics on mismatch and malformed patterns. Add IR layer unit tests.
- Verify: `pytest tests/unit_tests/ir -v`

## Read
- `agents/context/contract.md`
- `agents/context/tasks.yaml`
- `agents/context/tasks_state.yaml`
- `agents/context/project_status.md`
- `src/asdl/patterns.py`
- `src/asdl/ir/converters/nfir_to_ifir.py`
- `tests/unit_tests/ir/test_converter.py`
- `tests/unit_tests/ir/test_ifir_converter.py`
- `docs/specs/spec_asdl_pattern_expansion.md`

## Plan
1. Add shared pattern expansion helper(s) for endpoint tokens to reuse in binding verification.
2. Implement pattern binding verification in NFIR->IFIR conversion with diagnostics for invalid patterns and length mismatches.
3. Add IR unit tests covering scalar broadcast, patterned net mismatch, and malformed pattern diagnostics.
4. Run IR unit tests (or note if not run).

## Progress log
- 2026-01-09: Initialized scratchpad, read contract/specs and IR converters/tests; created feature branch; set T-058 in progress.
- 2026-01-09: Added endpoint pattern helper, binding verification in NFIR->IFIR conversion, and IR tests; updated existing pattern-preservation test for length matching; ran IR tests.

## Patch summary
- `src/asdl/patterns.py`: add endpoint expansion helper for inst.pin tokens.
- `src/asdl/ir/converters/nfir_to_ifir.py`: verify pattern binding lengths; emit IR-006 for mismatches; surface malformed pattern diagnostics.
- `tests/unit_tests/ir/test_ifir_converter.py`: add binding verification tests and adjust pattern-preservation fixture.

## Verification
- `venv/bin/pytest tests/unit_tests/ir -v`

## Status request
- Ready for Review

## Blockers / Questions
- None yet.

## Next steps
1. Implement endpoint expansion helper in `src/asdl/patterns.py`.
2. Add binding verification + diagnostics in `src/asdl/ir/converters/nfir_to_ifir.py`.
3. Write IR tests for mismatch and malformed patterns.
