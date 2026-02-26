# T-322 Scratchpad

## Goal
Thread module `parameters` through AST and core graph layers with deterministic behavior.

## Reuse audit checklist
- Reuse existing `parameters` naming conventions (`parameters`, not `params`).
- Reuse existing parameter value typing/normalization paths where available.
- Reuse existing lowering patterns for carrying module metadata through core graphs.

## Expected behavior
- `ModuleDecl.parameters` accepted in AST.
- PatternedGraph and AtomizedGraph module models carry `parameters`.
- Deterministic key order preserved through lowering.

## Verify
- `./venv/bin/pytest tests/unit_tests/ast/test_models.py tests/unit_tests/core/test_patterned_graph_builder.py tests/unit_tests/core/test_patterned_graph_lowering.py tests/unit_tests/core/test_patterned_graph_atomize.py -v`
