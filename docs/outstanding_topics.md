# Implemented vs Outstanding Review

Date: 2026-01-06

This document summarizes what is implemented vs outstanding relative to the
specs in `docs/specs/` and `docs/specs_mvp/` as observed in the codebase.

## Scope and sources
- Specs reviewed:
  - `docs/specs_mvp/spec_ast_mvp.md`
  - `docs/specs_mvp/spec_asdl_nfir_mvp.md`
  - `docs/specs_mvp/spec_asdl_ifir_mvp.md`
  - `docs/specs_mvp/spec_netlist_emission_mvp.md`
  - `docs/specs_mvp/spec_pipeline_mvp.md`
  - `docs/specs_mvp/spec_cli_mvp.md`
  - `docs/specs/spec_ast.md`
  - `docs/legacy/spec_asdl_nfir.md`
  - `docs/legacy/spec_asdl_ifir.md`
  - `docs/specs/spec_asdl_import.md`
  - `docs/specs/spec_asdl_pattern_expansion.md`
  - `docs/legacy/spec_compiler_stack.md`
  - `docs/specs/spec_diagnostics.md`
  - `docs/specs/spec_asdl_cir.md` (superseded)
  - `docs/specs/spec_asdl_nlir.md` (superseded)
- Code reviewed (primary):
  - `src/asdl/ast/`
  - `src/asdl/ir/`
  - `src/asdl/emit/netlist/`
  - `src/asdl/imports/`
  - `src/asdl/cli/`
  - `config/backends.yaml`

## Implemented (aligned to specs)
- AST schema and parser validation for MVP net-first surface:
  - Top-level `top`, `modules`, `devices`, net-first `nets`, flat `instances`,
    required `backends` per device, port inference from `$` nets.
  - Implemented in `src/asdl/ast/models.py` and `src/asdl/ast/parser.py`.
- NFIR dialect + AST->NFIR conversion (MVP):
  - Net-first topology, port order from `$` nets, instance expr parsing into
    `ref` + params, endpoint parsing, diagnostics for invalid tokens.
  - Implemented in `src/asdl/ir/nfir/dialect.py` and
    `src/asdl/ir/converters/ast_to_nfir.py`.
- IFIR dialect + NFIR->IFIR conversion (MVP):
  - Instance-first connectivity, named-only conns, nets explicit, conversion
    inverts endpoints into conns.
  - Implemented in `src/asdl/ir/ifir/dialect.py` and
    `src/asdl/ir/converters/nfir_to_ifir.py`.
- MVP pipeline orchestration (AST->NFIR->IFIR with optional verify passes):
  - Implemented in `src/asdl/ir/pipeline.py`.
- Netlist emission per MVP rules:
  - Backend-selected emission, system device templates, param merge ordering,
    named-only conns ordering by port lists.
  - Implemented in `src/asdl/emit/netlist/` and `config/backends.yaml`.
- CLI netlist command (`asdlc netlist`):
  - Input parsing, pipeline run, backend selection, output file handling,
    deterministic diagnostics rendering.
  - Implemented in `src/asdl/cli/__init__.py`.
- Diagnostics core and rendering contract:
  - Deterministic sorting and text/JSON renderers.
  - Implemented in `src/asdl/diagnostics/`.
- Import resolution core (spec v0.1):
  - Path resolution, ambiguity detection, cycles, ProgramDB, NameEnv.
  - Implemented in `src/asdl/imports/`.
- Pattern expansion engine + elaboration:
  - Expansion rules, binding length checks, and elaboration pass used by
    netlist emission.
  - Implemented in `src/asdl/patterns.py` and
    `src/asdl/ir/pattern_elaboration.py`.

## Outstanding or partial (by spec area)

### Imports (spec v0.1)
- Import resolution is not wired into the CLI or pipeline; the CLI does not
  accept `-I`/`--lib` roots and does not build `ProgramDB`/`NameEnv` before
  AST->NFIR.
- `file_id` propagation is not yet in IR types or conversions:
  - `entry_file_id` on design ops, `file_id` on module/device ops, and
    `ref_file_id` on instance ops are missing.
- Unused import lint (`LINT-001`) is not emitted end-to-end because imports
  are not consumed by the pipeline.

### AST (full spec vs MVP)
- `exports` block (port forwarding) from `docs/specs/spec_ast.md` is not
  implemented in AST models or lowering.
- Full pattern token rules in AST are only partially enforced (some are
  deferred to later passes; the parser does not yet enforce all pattern
  position constraints).

### NFIR / IFIR (pattern-preserving specs)
- Pattern-related metadata fields (expansion lengths, `port_len`) and
  verification rules from `docs/legacy/spec_asdl_nfir.md` and
  `docs/legacy/spec_asdl_ifir.md` are not implemented in the dialects.
- Equivalence checks based on expanded tokens are incomplete (there is a
  pattern-length check in NFIR->IFIR conversion, but not the full equivalence
  and verification contract).

### Netlist emission placeholders and disambiguation
- `{file_id}`, `{sym_name}`, `{top_sym_name}` placeholders are not supported
  in system-device template validation and rendering.
- Deterministic subckt name disambiguation for same-name modules across files
  is not implemented.

### Param value normalization
- MVP spec calls for boolean values to become `1`/`0` at AST->NFIR; current
  conversion uses `true`/`false` strings.

### Superseded specs
- `docs/specs/spec_asdl_cir.md` and `docs/specs/spec_asdl_nlir.md` are marked
  superseded by the current AST->NFIR->IFIR pipeline and are not implemented.

## Notes
- The MVP pipeline is functional end-to-end for single-file designs with
  explicit names and no imports.
- Import support exists as a library component but needs CLI/pipeline wiring
  to become user-facing.
