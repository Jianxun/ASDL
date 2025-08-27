# Generator TODOs

This file tracks the netlist generator refactor and behavior changes.

## In-Progress: Behavior Changes (MVP)

- Add top-level rendering modes via options/CLI:
  - subckt: emit `.subckt {top} … .ends` as the final section.
  - flat: comment out only the top `.subckt`/`.ends` wrapper lines with `*` (body unchanged).
- Emit hierarchical subckts in dependency order (children before parents), with `top` last. Use deterministic tie-breaking for orphans.

## Refactor Tasks

- Extract generator components:
  - options.py: `TopStyle` enum and `GeneratorOptions` dataclass. [DONE]
  - ordering.py: dependency graph + reverse topo ordering ensuring `top` last. [PENDING]
  - subckt.py: subckt builder (supports `flat` commenting of top wrapper). [DONE]
  - instances.py: instance renderer dispatch (primitive vs hierarchical). [DONE]
  - templates.py: primitive template rendering with var/param merge and G0601 warning. [DONE]
  - calls.py: hierarchical subckt call formatting (ordered nodes, sorted params). [DONE]
  - formatting.py: helpers and constants (port order, param formatting, indent/comment). [DONE]
  - guards.py: defensive checks for unknown model/missing mappings (G0401, G0201). [DONE]
  - postprocess.py: unresolved placeholder scan (G0305). [DONE]
- Slim `spice_generator.py` to orchestration only; remove PDK includes and XMAIN. [DONE]
- CLI: add `--top-style {subckt,flat}` and pass options to generator. [PENDING]

## Diagnostics and Unit Tests

The generator emits diagnostics (XCCSS) for defensive checks and postprocessing. Focused unit tests live under `tests/unit_tests/generator/` (one file per code):

- G0102: Top module not found (ERROR)
  - Trigger: `file_info.top_module` is set but absent from `modules`.
  - Behavior: emit diagnostic with missing name and available modules; annotate output with a comment.
- G0301: Invalid module definition (ERROR)
  - Trigger: module has neither `spice_template` nor `instances`.
  - Behavior: emit diagnostic; add a comment; skip generation for that module.
- G0201: Unconnected port in subckt call (ERROR)
  - Trigger: hierarchical instance missing mappings for declared child ports.
  - Behavior: emit diagnostic; add a comment; skip the offending instance line.
- G0401: Unknown model reference (ERROR)
  - Trigger: instance.model not found in `modules`.
  - Behavior: emit diagnostic; add a comment; skip the instance line.
- G0601: Variable shadows parameter (WARNING)
  - Trigger: primitive template render where a variable name overwrites a parameter.
  - Behavior: emit warning; variable takes precedence.
- G0305: Unresolved template placeholders (ERROR)
  - Trigger: `{placeholder}` remains after rendering.
  - Behavior: emit diagnostic listing unique placeholders.
- I0701: No top specified (INFO)
  - Trigger: `file_info.top_module` is None/empty.
  - Behavior: emit informational diagnostic; output remains a valid library ending with `.end`.

## Test Suite Updates (post-refactor)

- Remove assertions expecting `XMAIN` lines.
- Add ordering tests: children-before-parents; `top` subckt last.
- Add `flat` vs `subckt` top mode tests (commented wrappers vs normal wrappers for top only).
- Ensure no automatic PDK includes appear in generator output; PDK handling moved to orchestrator-level tests.
- Keep existing focused diagnostics tests (G0102/G0201/G0301/G0305/G0401/G0601/I0701) with updated expectations/messages.

## Completed/Cleaned Up

- Dropped legacy assumption of inferred PDK include paths in generator.
- Retired tests that asserted PDK include deduplication inside generator; these will be replaced by orchestrator/header injection tests later if needed.
 - Removed automatic PDK `.include` emission from generator output.
 - Removed `XMAIN` emission from generator output; preserved diagnostics for missing/unknown top.
 - Extracted generator into modular components: `options.py`, `subckt.py`, `instances.py`, `templates.py`, `calls.py`, `formatting.py`, `guards.py`, `postprocess.py`.
 - Refactored `SPICEGenerator.generate()` into focused helper methods (header/invalids/subckts/top_diag/end).
 - Kept thin wrapper methods for `generate_subckt`/`generate_instance` to maintain unit test API.
 - Updated unit tests to remove expectations about auto-includes; all generator unit tests passing (18/18).

## Dependency Ordering Algorithm

- Build the DAG
  - Nodes: hierarchical modules only (`module.instances is not None`).
  - Edges: parent → child for each instance whose `instance.model` is hierarchical (skip primitives).
  - Source: `asdl_file.modules` provides deterministic iteration (insertion order); fall back to name-sorted if needed.

- Ordering (children-first, top last)
  - Use DFS postorder with cycle detection:
    - `temp_mark` (on recursion stack) and `perm_mark` (fully visited) sets.
    - Visit all hierarchical children first; append the parent to `ordered` when done.
  - Handle `top` explicitly:
    - Run DFS from `top` to get `reachable_by_top` (postorder → `top` naturally last in that subgraph).
    - For remaining hierarchical modules not reachable from `top`, run DFS in deterministic order and append results.
    - Final emission: `reachable_by_top` excluding `top`, then all orphan groups, then `top` as the very end.

- Multiple references and deduplication
  - The `perm_mark` set ensures each module emits exactly one `.subckt`, even if referenced by multiple parents.

- Cycles (invalid hierarchy)
  - Encountering a node already in `temp_mark` indicates a cycle. Emit a generator diagnostic (e.g., recursive hierarchy detected) and skip the back-edge to terminate traversal safely. Validator should normally catch this earlier.

- Determinism
  - Iterate children using module insertion order (or name-sorted) to keep stable output across runs.

- Top-style interaction
  - `subckt`: emit wrappers for all modules; `top` last.
  - `flat`: same order, but comment only the `top` `.subckt`/`.ends` lines with `*`; keep body intact.
