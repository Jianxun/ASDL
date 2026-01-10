Title: ADR-0008: Module-Local Named Patterns
Status: Accepted

## Context
Complex pattern expressions are error-prone and verbose when repeated. We want
to encapsulate commonly used pattern groups with a single token.

## Decision
Add module-local named pattern definitions and a dedicated reference token.

Shape:
```yaml
patterns:
  <name>: <pattern-group>
```

Reference syntax:
```
<@name>
```

Rules:
- `patterns` are module-local only (no document-level sharing).
- `<@name>` may appear anywhere pattern tokens are allowed.
- Pattern values must be a **single group token**: either `<...>` (enum) or
  `[...]` (range). Splice (`;`) is not allowed inside named patterns.
- Named patterns must not reference other named patterns (no recursion).
- Undefined names are diagnostics.

Architecture:
- Resolve `<@name>` by macro substitution during AST elaboration **before**
  AST->NFIR conversion and before pattern verification.

## Consequences
- Adds a lightweight macro expansion stage in the front-end.
- Keeps pattern elaboration logic unchanged after substitution.

## Alternatives
- Global/shared named patterns. Rejected: scoping ambiguity and import
  interactions.
- Allow full pattern expressions (including `;`) as named patterns. Rejected:
  `<@name>` is a group token, so splicing would be ambiguous without a second
  reference form.
