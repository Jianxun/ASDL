# ADR-0013: Atomized inversion for NFIR -> IFIR

Status: Accepted

Context
- Subset endpoint tokens (e.g., `MP_LOAD<P>` from `MP_LOAD<P|N>`) are common and
  should resolve to the correct atomized instance.
- ADR-0012 fixed NFIR endpoint validation, but NFIR->IFIR inversion still
  collapses endpoint conns onto the patterned instance token.
- PatternAtomizePass then expands those conns to every atom, which can create
  duplicate port connections in IFIR verification.

Decision
- NFIR->IFIR conversion atomizes instance/net/endpoint tokens and builds IFIR
  instance conns per atom, so subset endpoints bind only to the intended atom.
- Atomized IFIR names carry `pattern_origin` metadata for grouping.
- PatternAtomizePass remains in the pipeline but must be idempotent or skip
  modules that are already atomized.

Consequences
- IFIR may contain only atomized instance/net names after NFIR lowering.
- Converter tests must expect atomized names instead of raw pattern tokens.
- PatternAtomizePass becomes a no-op in the normal pipeline but remains useful
  for standalone IFIR ingestion.

Alternatives
- Encode endpoint ownership in IFIR conns: rejected due to dialect complexity.
- Move atomization before NFIR verification: rejected because NFIR remains
  pattern-preserving by contract.
