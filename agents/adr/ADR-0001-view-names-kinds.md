# ADR-0001: Reserved view names and kinds

- Status: Superseded
- Date: 2025-12-28
- Superseded by: `docs/specs/spec_ast.md` and `docs/specs/spec_asdl_cir.md` (canonical v0 view kinds)

## Context
- The ASDL refactor makes views first-class; selection operates on `(module, view)`.
- Initial reserve set did not include `behav`; revised specs promote `behav` as a canonical v0 kind and formalize dummy/subckt_ref constraints.

## Superseded Decision (for history)
- Reserved view names: `nominal` (canonical default; `nom` alias accepted) and `dummy`. All other view names are user-defined.
- Reserved view kinds (superseded): `subckt`, `subckt_ref`, `primitive`, `dummy`; `pex` as `subckt_ref` specialization.

## Current Decision (per spec v0)
- Reserved view names remain: `nominal` (alias `nom` optionally) and `dummy`.
- Canonical v0 view kinds: `{subckt, subckt_ref, primitive, dummy, behav}`; `behav` is supported for externally evaluated models.
- Dummy is restricted in v0 to empty or a single `weak_gnd` mode; structural/template dummy is deferred to v0.1+.
- `subckt_ref` assumes identity pin_map when omitted; explicit pin_map required for positional external pin orders.
- Multiple views may coexist; exclusivity is resolved by the SelectView pass, not the schema.

## Consequences
- Contract/task/spec work must follow the canonical v0 kind set from the specs, not the superseded set.
- ADR-0001 is retained for provenance; consult the specs for authoritative rules.

## Alternatives
- n/a (superseded by specs)
