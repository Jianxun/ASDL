# T-065 Pattern enumeration validation

## Task summary
- **DoD**: The pattern expander/parser rejects enumeration tokens that use invalid delimiters (e.g., commas instead of `|`) so malformed inputs like `MN_OUT<P,N>` fail quickly with PASS diagnostics before NFIR verification. Include parser/IR tests validating the new error and keeping the valid expansion suite intact.
- **Verify**:
  - `pytest tests/unit_tests/parser -v`
  - `pytest tests/unit_tests/ir -v`

## Read
- `docs/specs/spec_asdl_pattern_expansion.md`
- `src/asdl/patterns.py`
- `src/asdl/ir/converters/nfir_to_ifir.py`
- `tests/unit_tests/parser/test_pattern_expansion.py`
- `tests/unit_tests/ir/test_ifir_converter.py`

## Plan
1. Confirm `_validate_enum_content` currently allows commas and determine the right diagnostic code (`PATTERN_UNEXPANDED` or similar) for a malformed enumeration.
2. Harden `expand_pattern`/`_validate_enum_content` to reject commas (and any other forbidden characters) inside `<...>` and add unit tests showing `MN_OUT<P,N>` fails while `MN_OUT<P|N>` still passes.
3. Ensure upstream NFIR verification and binding diagnostics see the new validation by adding parser-level tests or IR fixtures where a malformed enumeration now produces a PASS error code (instead of falling through to binding mismatch).
4. Run the parser/IR test suites listed above.

## Progress log
- Not started yet.

## Status request
- None.

## Blockers / Questions
- None.

## Next steps
1. Update `_validate_enum_content` to reject commas inside `<...>` with a clear message per the spec.
2. Hook in diagnostics/tests so malformed enumerations fail before binding verification.
