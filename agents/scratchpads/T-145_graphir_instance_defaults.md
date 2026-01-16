# Task summary (DoD + verify)
- Task: T-145 Apply instance_defaults in AST->GraphIR lowering
- DoD: Consume module `instance_defaults` during AST->GraphIR lowering by injecting default endpoints and nets, emitting override warnings (with `!` suppression), and extending `port_order` with `$` nets introduced by defaults after explicit net ports. Preserve pattern atomization semantics and add unit tests for defaults, overrides, and port ordering.
- Verify: venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v

# Read (paths)
- agents/context/lessons.md
- agents/context/contract.md
- agents/context/tasks.yaml
- agents/context/tasks_state.yaml
- agents/context/project_status.md
- agents/adr/ADR-0007-instance-defaults.md
- docs/specs/spec_ast.md
- legacy/src/asdl/ir/converters/ast_to_nfir.py
- src/asdl/ast/models.py
- src/asdl/ast/named_patterns.py
- src/asdl/ast/parser.py
- src/asdl/ir/converters/ast_to_graphir.py
- src/asdl/ir/converters/ast_to_graphir_lowering.py
- src/asdl/ir/converters/ast_to_graphir_lowering_instances.py
- src/asdl/ir/converters/ast_to_graphir_lowering_nets.py
- src/asdl/ir/converters/ast_to_graphir_parsing.py
- src/asdl/ir/patterns/atomize.py
- tests/unit_tests/ir/test_graphir_converter.py

# Plan
- [x] Add GraphIR converter tests for instance_defaults (apply, override warning/suppression, port order).
- [x] Extend GraphIR lowering to merge instance_defaults into nets and port_order.
- [x] Run targeted IR converter tests and summarize results.

# Progress log
- Created scratchpad, set task status to in_progress, and created feature branch.
- Added GraphIR converter tests for instance_defaults defaults/overrides/port order.
- Updated GraphIR lowering and parsing to wire instance_defaults and override warnings.
- Ran targeted GraphIR converter tests.
- Fixed parse_endpoints error return regression and reran tests after review feedback.

# Patch summary
- Added GraphIR converter coverage for instance_defaults defaults, override warnings/suppression, and port order.
- Applied instance_defaults in GraphIR net lowering, including override warnings and port_order updates.
- Extended endpoint parsing to carry override suppression flags.

# PR URL
- https://github.com/Jianxun/ASDL/pull/154

# Verification
- ./venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v
- ./venv/bin/pytest tests/unit_tests/ir/test_graphir_converter.py -v

# Status request (Done / Blocked / In Progress)
- Done

# Blockers / Questions
- TBD

# Next steps
- TBD
