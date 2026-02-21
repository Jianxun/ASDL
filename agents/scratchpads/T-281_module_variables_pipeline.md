# T-281 - module variables pipeline propagation

## Task summary
- Preserve `module.variables` through PatternedGraph and AtomizedGraph.
- Ensure lowering carries module variable maps forward unchanged.

## Verify
- `./venv/bin/pytest tests/unit_tests/core tests/unit_tests/lowering/test_atomized_graph_to_netlist_ir.py -v`
