# AST-022: Named pattern recursion

Command:
```sh
asdlc netlist case.asdl
```

Note: The parser currently rejects `<@...>` pattern values during AST validation
(PARSE-003). A harness that bypasses validation is required to surface AST-022.
