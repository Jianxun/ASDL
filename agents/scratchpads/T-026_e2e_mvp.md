# T-026 — End-to-End MVP Pipeline Test

## Goal
Add an end-to-end test: ASDL_A → ASDL_NFIR → ASDL_CIR → ASDL_NLIR_E → emit.

## References
- `docs/specs/spec_compiler_stack.md`

## Notes
- Validate determinism, port-order propagation, and NLIR `elab_state` usage.

## File hints
- `tests/unit_tests/e2e/`
- `examples/`

## Verify
- `pytest tests/unit_tests/e2e` (assert port-order propagation and NLIR `elab_state`)
