# ADR-0012: NFIR endpoint resolution uses atomized equivalence

Status: Accepted

Context
- Common authoring uses subset pattern endpoints (e.g., `MN_IN_<N>`) that refer to
  instances declared as broader patterns (e.g., `MN_IN_<P|N>`).
- ADR-0011 atomizes patterns after NFIR->IFIR, but NFIR verification and the
  NFIR->IFIR inverter still require literal instance-token matches, causing the
  pipeline to fail before atomization.

Decision
- NFIR module verification resolves endpoint instance tokens via atomized
  literal equivalence and treats missing literals as unknown instances.
- NFIR endpoint uniqueness is checked on atomized `(inst_literal, pin_literal)`
  pairs to detect collisions created by overlapping pattern tokens.
- NFIR->IFIR conversion uses the same atomized literal map to attach endpoint
  connections to the owning instance op, even when the endpoint token is a
  subset of the instance pattern token.

Consequences
- Subset endpoint patterns are valid in NFIR and flow through the pipeline.
- Literal collisions are detected early with deterministic errors.
- Verification and conversion incur atomization cost, but atomization remains a
  dedicated pass before emission.

Alternatives
- Move pattern atomization before NFIR verification: rejected because it breaks
  the pattern-preserving NFIR/IFIR contract.
- Require endpoints to use the exact instance token: rejected due to common
  authoring patterns and ergonomics.
