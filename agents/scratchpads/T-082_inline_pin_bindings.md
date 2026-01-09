# T-082 Inline pin bindings in AST->NFIR conversion

## Objective
Support inline pin bindings in instance expressions, normalize them into net-first NFIR, and allow `$` inline nets to create ports with deterministic ordering.

## DoD
- Parse `(<port>:<net> ...)` whitespace-separated bindings from instance expressions.
- Merge inline bindings into the module net map (create nets as needed).
- `$`-prefixed inline net names create ports if not declared in `nets`.
- Port order is `$` nets from `nets` first, then `$` nets first-seen in inline bindings.
- Emit conversion diagnostics for malformed pin-binding tokens and for endpoints bound in both `nets` and inline bindings.
- MVP AST/NFIR specs updated to allow inline bindings and describe the rules.
- Unit tests cover inline bindings, overlap errors, and inline-created ports.

## Files
- src/asdl/ir/converters/ast_to_nfir.py
- tests/unit_tests/ir/test_converter.py
- docs/specs_mvp/spec_ast_mvp.md
- docs/specs_mvp/spec_asdl_nfir_mvp.md

## Verify
- pytest tests/unit_tests/ir/test_converter.py -v

## Notes
- Inline bindings are equal to `nets` bindings; overlap is an error.
- Inline `$` nets only create ports; they do not affect non-$ nets.
