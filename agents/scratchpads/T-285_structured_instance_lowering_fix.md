# T-285 Structured Instance Lowering Fix

## Goal
Fix AST-to-PatternedGraph lowering so structured instance declarations (`ref` + `parameters`) follow the same normalization path as inline instance strings.

## Notes
- Reuse shared instance parsing helpers.
- Do not allow raw exceptions for malformed instance payloads.
- Emit lowering diagnostics with source spans when available.

## Verify
- `./venv/bin/pytest tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/e2e/test_pipeline_mvp.py -v`
