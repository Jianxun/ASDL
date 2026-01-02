 # xDSL Development Style Guide (ASDL)

 Guidance for building and evolving ASDL's xDSL stack (dialects, passes, tooling) while keeping room for executor-level implementation choices. This is style- and practice-focused; avoid over-prescribing APIs here.

 ## Scope & Principles
 - Python-first, MLIR-compatible: author in Python, but keep textual IR stable/deterministic for review and goldens. (Optional reference: xdsl.dev)
 - AST is a shape gate; xDSL IR is the semantic source of truth.
 - Determinism over cleverness: stable operation ordering, no hidden randomness.
 - Round-trip is not guaranteed: elaboration/lowering may be lossy; design passes with clear invariants instead of reversible transforms.
 - Small surface, sharp edges: few well-named ops/attrs with strong verifiers and good diagnostics.
 
 ## Dialect & Op Design
 - Naming: prefer `asdl_<layer>` dialects (e.g., `asdl_nfir`, `asdl_ifir`); op names should match spec roles (DesignOp, ModuleOp, InstanceOp, NetOp).
 - Operands vs attributes: for netlist IRs, topology and conns live in attributes (named-only conns). Use operands only for SSA/dataflow modeling.
 - Types/attrs: keep attribute schemas explicit (lists/maps, not dict-ordered assumptions); preserve declared port order explicitly when needed.
 - Locations: thread source locations from AST into ops; favor file+span locations for diagnostics.
 - Verifiers: enforce invariants early; prefer verifier errors over late pass failures.
 - Extensibility: keep optional attributes future-proof (use explicit defaults, avoid sentinel magic strings).
 
 ## Pass & Pipeline Style
 - Pipeline order should stay readable and documented (MVP: AST -> NFIR -> IFIR -> emit).
 - Passes are single-responsibility and idempotent where feasible; clearly document if a pass is intentionally lossy.
 - Avoid pass-time global state; rely on IR contents and pass options.
 - When passes must drop info (e.g., elaboration), note the contract and expected outputs; do not promise reversibility.
 - Prefer analyses feeding later passes to ad-hoc mutations.
 
 ## Diagnostics & Locations
 - Use shared diagnostic contracts (code, severity, primary span, labels/notes/help).
 - Fail with diagnostics, not exceptions, for user-facing issues; only assert for programmer errors.
 - Keep diagnostic ordering deterministic to stabilize tests.
 
 ## Testing Guidance
 - Unit tests per op/attr verifier and per pass; include negative cases that surface diagnostics.
 - Golden-text tests for IR printers (deterministic formatting, stable attribute ordering).
 - Skip xDSL-dependent tests gracefully when the optional dependency is missing.
 - Keep fixtures small and focused; prefer one expectation per test file when tied to a diagnostic code.
 
 ## File & Layout Conventions
 - Dialects live under `src/asdl/ir/<layer>/` (e.g., `src/asdl/ir/nfir/`, `src/asdl/ir/ifir/`).
 - Converters live under `src/asdl/ir/converters/`.
 - Tests mirror package layout under `tests/unit_tests/ir/`.
 - CLI/driver glue belongs in `src/asdl/cli/` (or nearest equivalent), not inside dialect modules.
 
 ## CLI & Tooling Integration
 - Add `ir-dump`/`--verify`/`--run-pass` style hooks for inspection and debugging; keep outputs deterministic.
 - Default to project venv (`venv/`) for tooling and tests.
 
 ## References
 - ASDL MVP specs: `docs/specs_mvp/` (AST, NFIR, IFIR, emission)
 - Project contract and tasks: `agents/context/contract.md`, `agents/context/tasks.md`, `agents/context/okrs.md`
