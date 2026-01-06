# T-064 Pattern endpoint equivalence

## Task summary
- **DoD**: NFIR verification uses pattern-expansion equivalence instead of raw string equality so that instances like `MN_OUT<P,N>` bind the same as endpoints using `MN_OUT<P|N>`. Coverage comes from targeted IR unit tests plus a netlist CLI invocation over `examples/scratch/test.asdl`.
- **Verify**:
  - `pytest tests/unit_tests/ir -v`
  - `./venv/bin/asdlc netlist examples/scratch/test.asdl`

## Read
- `agents/context/contract.md`
- `docs/specs/spec_asdl_pattern_expansion.md`
- `src/asdl/ir/nfir/dialect.py`
- `src/asdl/ir/converters/nfir_to_ifir.py`
- `tests/unit_tests/ir/test_ifir_converter.py`
- `examples/scratch/test.asdl`

## Plan
1. Understand how `ModuleOp.verify_` currently maps endpoint tokens to instance names; locate where the mismatch happens when tokens differ but expansions line up.
2. Introduce a helper (likely in `src/asdl/patterns.py` or a new utility) so the verification can compare expansion lists for both instance and endpoint tokens.
3. Update NFIR verification and/or the IR converter to use the helper, emit diagnostics when the helper fails, and ensure the CLI/netlist pipeline respects the new equivalence.
4. Extend `tests/unit_tests/ir/test_ifir_converter.py` (or another suitable IR test) to cover the mismatched token scenario and guard against regressions.

## Progress log
- Not started yet.

## Status request
- None.

## Blockers / Questions
- None.

## Next steps
1. Sketch master helper for comparing pattern expansions (reuse `expand_pattern`/`expand_endpoint` if possible).
2. Wire the helper into NFIR verification to catch mismatches before IFIR lowering.
3. Add regression tests and run the IR/netlist commands listed above.
