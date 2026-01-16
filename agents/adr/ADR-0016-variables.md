# ADR-0016: Variables blocks and parameter key rename

Status: Accepted

## Context
The authoring AST currently exposes device parameter defaults and backend
overrides via a `params` block. We need module- and device-scoped constants
that can be referenced in instance parameter values and backend templates, and
we want consistent, non-abbreviated schema naming.

## Decision
- Introduce `variables` blocks at the module, device, and device-backend scopes.
  Values use the same `ParamValue` type as parameters.
- Variables are immutable at instantiation time; instance parameters must not
  override variable values.
- Module variables are referenced only inside instance parameter values using
  `{var}` placeholders. Substitution is raw string replacement (no expression
  evaluation), allows references to other variables, and forbids recursive
  cycles (emit diagnostics on cycles or undefined variables).
- Device/backend variables are exposed as `{var}` placeholders in backend
  templates alongside parameters and backend props.
- Rename the AST schema key `params` to `parameters` for device defaults and
  backend overrides. No abbreviated alias is accepted.

## Consequences
- Authoring files must replace `params` with `parameters` (breaking change).
- AST models, parser, and specs need to add `variables` and `parameters` fields.
- AST -> GraphIR lowering must substitute module variables in instance parameter
  values before parameter pattern expansion.
- Emission must include variable placeholders when rendering device backends.

## Alternatives
- Keep `params` and add `variables` only for devices: rejected due to naming
  inconsistency and the need for module-local scaling constants.
- Evaluate arithmetic expressions in variables (e.g., `2*{k}`): rejected until
  a formal expression language is defined.
