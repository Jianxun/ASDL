## Validator Coverage Gaps and Next Tasks (MVP pre-release)

### Principles
- Validator owns structural/semantic checks on elaborated IR (component prefix: V).
- Generator keeps minimal runtime safeguards; no duplication of responsibility.
- One file per code in tests: `tests/unit_tests/validator/test_vXXXX_*.py`.

### Proposed New Rules (codes and intent)
- **Port mappings**
  - V0306 Missing required mappings: instance omits required target ports.
  - V0307 Empty/None net names: mapping value is missing/blank.
  - V0202 Port/internal-net name collision: name appears in both `ports` and `internal_nets` of a module.

- **Module/model references and reachability**
  - V0402 Unknown local model: instance `model` not defined in-file and not recognized as primitive (post-import).
  - V0403 Recursive instantiation cycle: detect self/indirect cycles in module graph.
  - V0605 Unreachable-from-top modules: compute reachability from `file_info.top_module` and warn for orphan modules (refine current unused logic).

- **Nets quality and connectivity**
  - V0602 Unused internal nets: declared but never referenced by any instance mapping in the module.
  - V0404 Connectivity quality (heuristic): floating nets or multi-driver situations within a module (WARNING; lightweight analysis only).

- **Parameters/variables quality**
  - V0603 Unused parameters: declared but never overridden nor used by template placeholders (best-effort until full type system).
  - V0604 Unused variables: declared but not referenced downstream.
  - V0501 Parameter value validation: basic type/format/unit checks once parameter typing metadata exists (future).

- **Top/module-level invariants**
  - V0203 Invalid `top_module`: top set but missing in `modules` (consider moving earlier than generator G0102).
  - V0204 Module name hygiene: duplicate/conflicting names across combined IR (future multi-file validation scope).

- **Template alignment (preflight)**
  - V0309 Placeholder mismatch: instance overrides names not used by the primitive `spice_template`, or template placeholders with no available source (early WARNING mirror of generator G0305).

### Implementation Plan (next session)
- Add rules in `src/asdl/validator/rules/` for each code above (start with V0306, V0307, V0402, V0602, V0605).
- Register in `core/registry.py`; keep severities per policy (V06xx → WARNING, V05xx → ERROR unless noted).
- Add per-code tests under `tests/unit_tests/validator/` following the new style.
- Update docs: `src/asdl/validator/diagnostics.py` registry entries for titles/details; add to `doc/diagnostic_system/` index if needed.

### Notes on non-overlap policy
- Keep generator checks (e.g., G0201, G0305) as last-resort; validator will preflight common user mistakes.
- CLI continues to run validator first and may skip generation on ERRORs.

### Open Questions
- Should V0404 attempt graph-level electrical rules (multi-driver) now or defer to a dedicated electrical linter later?
- Define primitive recognition for V0402: treat missing local module as primitive by default or require an allowlist?

