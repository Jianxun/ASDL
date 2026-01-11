# ADR-0011: Pattern atomization and literal collision rules

Status: Accepted

Context
- Patterns carry semantic grouping for devices and ports.
- Authors need to bind subsets of patterned instances/nets (e.g., `MN_<N>` from `MN_<P|N>`).
- The current flow keeps multi-atom patterns until emission, which blocks subset endpoint bindings and loses grouping when expanded to literals.
- Different pattern forms can emit identical literals (e.g., `MN_<1>` vs `MN_[1]`), which would silently collide in netlists.

Decision
- Introduce a PatternAtomize pass that expands multi-atom patterns into single-atom
  pattern tokens (e.g., `MN_<P|N>` -> `MN_<P>`, `MN_<N>`; `BUS[2:0]` -> `BUS[2]`,
  `BUS[1]`, `BUS[0]`) before IFIR verification/emission.
- Allow base-less patterns (`<INP|INN>`, `[2:0]`) wherever pattern syntax is permitted.
- Preserve grouping semantics via `pattern_origin` metadata on atomized nets/instances.
- Endpoint instance validity uses subset-of-atoms: endpoint atoms must resolve to
  declared instance atoms.
- Enforce literal-name uniqueness within instance names and within net names;
  collisions are fatal errors even across different pattern origins. No implicit
  literal/pattern equivalence is allowed.

Consequences
- Enables partial connectivity on patterns while preserving grouping metadata.
- Detects ambiguous or colliding names early and avoids silent netlist merges.
- Requires an atomization pass, updated IFIR ops, and revised tests; emission no
  longer performs pattern expansion.

Alternatives
- Expand to literal strings only or allow literal-name equivalence: rejected
  because both weaken grouping semantics and allow silent merges.
- Name-mangle on collision: rejected because it breaks author intent and
  external netlist matching.
