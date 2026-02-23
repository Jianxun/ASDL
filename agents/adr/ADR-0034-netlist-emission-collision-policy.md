# ADR-0034: Netlist Emission Name Collisions Use DFS-Stable Ordinal Suffixes

- Status: Accepted
- Date: 2026-02-23

## Context
ASDL supports view-decorated module symbols (`cell@view`) and qualified
references across multiple files, so semantic symbol resolution is unambiguous.
However, flat simulator netlists require globally unique emitted subckt/module
names. The previous hash-based disambiguation policy was deterministic but less
readable and depended on file-ID hashing strategy.

We need a collision strategy that:
- preserves existing deterministic emission order
- keeps emitted names human-inspectable
- handles collisions between decorated realizations and literal module names
- preserves provenance for debugging/integration

## Decision
Adopt a DFS-order, ordinal-suffix collision policy for emitted module names.

1. Realization base names:
   - `cell` for undecorated symbols and `cell@default`
   - `cell_<view>` for non-default decorated symbols

2. Allocation order:
   - process modules in deterministic emission traversal order
   - do not reorder modules for collision grouping

3. Uniqueness rule:
   - keep a global set of assigned emitted names
   - assign `base` if unused
   - otherwise assign `base__2`, `base__3`, ... until unique

4. Collision scope:
   - applies to all emitted modules, including collisions where a decorated
     realization base (for example `cell_<view>`) clashes with an existing
     undecorated module name

5. Provenance and observability:
   - backend subckt headers should include `{file_id}` for source provenance
   - emitters should warn on collision suffixing and should provide a
     deterministic logical-to-emitted name mapping artifact

## Consequences
- Positive: preserves deterministic output and existing DFS-style readability.
- Positive: emitted names remain concise and manually inspectable (`__2`, `__3`)
  without opaque hashes.
- Tradeoff: ordinal suffixes depend on traversal order; inserting earlier
  colliding modules can renumber later emitted names.

## Alternatives
- Hash-based disambiguation (`__hash8`): rejected as less human-readable and
  noisier for manual netlist debugging.
- Strict fail-on-collision: rejected for v0 because multi-file/IP integrations
  may legitimately require automatic disambiguation.
