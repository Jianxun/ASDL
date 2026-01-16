# T-139 Module-local named pattern macro expansion

## Goal
Implement `<@name>` macro substitution as an AST elaboration step before
AST->GraphIR lowering, following ADR-0008 rules.

## Notes
- Substitution is textual and must happen before pattern expansion/verification.
- Named patterns are module-local and must be single group tokens.
- No recursion; undefined names are diagnostics.
