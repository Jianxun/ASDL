### ASDL Simulation Referencing & Hierarchy – Discussion Summary

This note summarizes our design discussion about stable referencing of ngspice vectors, preserving canonical hierarchy in `asdlc`, and enabling non-destructive subtree substitution. It also captures relevant aspects of the current `asdlc` implementation for context.

## Problem: Flattened ngspice vectors cause friction
- **Hierarchy loss**: Simulator vector names are flattened; hierarchical intent (instance/port/terminal context) is lost.
- **Instability**: Small netlist changes can alter flattened names and break analysis scripts.
- **Type ambiguity**: Mixing waveforms (V/I) and OP scalars without capability checks leads to invalid queries.
- **Namespace collisions & coupling**: Direct reliance on sim-specific names couples tooling to ngspice internals and hinders portability.

## Current asdlc architecture (context)
- **Data structures** (`src/asdl/data_structures/structures.py`):
  - `ASDLFile`, `Module`, `Instance`, `Port`, with unified module model (primitive via `spice_template` vs hierarchical via `instances`).
  - `Module` enforces mutual exclusivity of `spice_template` and `instances`.
- **Elaborator** (`src/asdl/elaborator/elaborator.py`):
  - `elaborate_with_imports(main_file_path, search_paths, top)` → resolves imports, expands patterns, resolves env vars and variables; returns elaborated `ASDLFile` + diagnostics.
- **Generator** (`src/asdl/generator/spice_generator.py`):
  - Emits `.subckt` per hierarchical `Module`, instances via `instances.py`, primitives via `templates.py`.
  - Orders modules by dependency; top module wrappers controlled by options.

## Agreed strategy to resolve friction
1. **Canonical References (CRef)** as stable identifiers
   - Use hierarchical, canonical paths rooted at `top` for public references (e.g., `top.ota1.v(out)`, `top.ota1.m1.i(d)`, `top.ota1.m1.op(gm)`).
   - Results should be keyed by CRef; mapping to sim-specific names is adapter work.

2. **DesignTree artifact (post-elaboration)**
   - Build a canonical, typed instance tree after elaboration and before generation.
   - Keep separate from `Module`/`Instance`; index by path for fast lookup.
   - Proposed structures (new `src/asdl/elaborator/design_tree.py`):
     - `DesignTree`: `root`, `by_path: Dict[str, InstanceNode]`.
     - `InstanceNode`: `path`, `name`, `module_name`, `module_ref`, `parameters_resolved`, `ports_ref`, `internal_nets`, `children`, `parent`, `loc`.
   - Path rules: root is `top`; child path uses post-expansion ids: `parent.path + "." + instance_id`.

3. **Lazy CRef→sim-name binding via adapter (later phase)**
   - Generator can emit a sidecar `cref_index.json` mapping CRef → current sim symbol(s) (voltages, currents, OP scalars).
   - Bind handles after each netlist; rebind on re-netlist for stability.

4. **Library-first API with CLI wrapper**
   - Provide a `Session` object (e.g., `src/asdl/sim/session.py`) that runs elaboration, builds `DesignTree`, generates netlists, and later runs analyses.
   - Keep CLI (`asdl netlist`, `asdl transform`, …) as thin wrappers over the library to ensure identical behavior in REPL/Notebook and CLI.

## Subtree substitution: non-destructive overlay
- **Requirement**: Toggle substitution on/off while experimenting; avoid destructive edits to the elaborated design.
- **Solution**: Substitution overlay applied at netlisting time:
  - `SubstitutionPlan`: map instance-path (or subtree prefix) → `{ replacement_model, param_overrides? }`.
  - Validate interface compatibility (port names/order). If incompatible, require an adapter module.
  - Apply overlay by deep-copying the elaborated `ASDLFile` to a temporary view, swapping `instance.model` and merging parameters for matched paths; original remains intact.
  - Optionally produce both baseline and substituted netlists for A/B runs.
- **Implementation hook**: `Session.set_substitution(plan)`, `Session.clear_substitution()`, `Session.netlist(baseline=True/False)`, `Session.netlist_both(...)`.

## Why this fits asdlc now
- Does not change parser/elaborator/generator contracts; all changes are additive.
- Elaborator remains the source of truth for post-expansion instance ids; `DesignTree` freezes canonical paths.
- Generator keeps emitting from `ASDLFile`; overlays are expressed as an ephemeral, copied `ASDLFile` view.
- Sets up a clean seam for stable CRefs and backend-agnostic adapters later (rawfile or shared-lib).

## Minimal next steps
1. Add `DesignTree` builder and index (`src/asdl/elaborator/design_tree.py`).
2. Introduce `Session` with `netlist()` and non-destructive `substitute(...)` overlay.
3. Optional: CLI flags to emit both baseline and substituted netlists in one run.
4. Later: emit `cref_index.json` from generator and add adapter to bind CRefs → sim names.

## Appendix: Current files of interest
- `src/asdl/data_structures/structures.py`
- `src/asdl/elaborator/elaborator.py`
- `src/asdl/generator/spice_generator.py`
- `src/asdl/generator/subckt.py`, `instances.py`, `templates.py`


