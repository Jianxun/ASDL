# AST to GraphIR Architecture Review

**Date**: 2026-01-19  
**Reviewer**: Architect Agent  
**Context**: Post-T-170/T-171/T-172 (tagged pattern axes and broadcast binding)

## Executive Summary

Reviewed the AST→GraphIR conversion architecture in response to questions about:
1. Whether to bring NFIR back into the main pipeline
2. Whether to allow incomplete GraphIR with elaboration passes

**Recommendation**: Neither. Instead, decompose the converter internally while preserving the current pipeline (AST→GraphIR→IFIR→emit).

---

## Current Architecture

### File Structure

| File | LOC | Responsibility |
|------|-----|----------------|
| `ast_to_graphir.py` | ~150 | Entry points (`convert_document`, `convert_import_graph`) |
| `ast_to_graphir_context.py` | ~190 | Session/document contexts |
| `ast_to_graphir_lowering.py` | ~220 | Orchestration |
| `ast_to_graphir_lowering_instances.py` | ~590 | Instance lowering + symbol resolution |
| `ast_to_graphir_lowering_nets.py` | **~1110** | Net/endpoint lowering + axis broadcast |
| `ast_to_graphir_symbols.py` | ~200 | ID allocation, symbol tables |
| `ast_to_graphir_parsing.py` | ~100 | Token parsing helpers |
| `ast_to_graphir_utils.py` | ~50 | Diagnostic helpers |

### Primary Concern

`ast_to_graphir_lowering_nets.py` is ~1100 lines with a single function `lower_module_nets` spanning ~500 lines. It merges three distinct concerns:

1. **Core net binding**: Iterating nets, splitting tokens, creating NetOp/EndpointOp
2. **Axis metadata extraction**: `_axis_metadata`, `_collect_named_pattern_axes` (~200 lines)
3. **Tagged-axis broadcast mapping**: `_axis_broadcast_mapping` (~150 lines)

---

## Option 1: Bringing NFIR Back into Pipeline

### Proposed Change
```
Current:  AST → GraphIR → IFIR → emit
Proposed: AST → NFIR → GraphIR → IFIR → emit
```

### Analysis

**Arguments For:**
- NFIR is "net-first" and closer to the authoring model
- Could serve as intermediate step for pattern expansion before GraphIR
- Modular pipeline stages could be easier to test in isolation

**Arguments Against:**
- **Doesn't solve the core problem**: The complexity is in pattern/axis handling, not in IR shape. Moving to NFIR would relocate `lower_module_nets`'s complexity to `nfir_to_graphir`.
- **Duplicated verification**: Pattern/axis logic would need to exist in NFIR construction AND NFIR→GraphIR conversion.
- **Violates ADR-0014**: GraphIR is the canonical semantic core. Adding required NFIR means semantic decisions get spread across two IRs.
- **More conversion code**: Three converters instead of two.
- **Historical context**: NFIR was deprecated for a reason—it wasn't pulling its weight.

### Verdict: ❌ Not Recommended

---

## Option 2: Incomplete GraphIR with Elaboration Passes

### Proposed Change
Build GraphIR with one direction of mapping populated (e.g., nets with unresolved endpoints), then use xDSL passes to derive reverse mappings.

### Analysis

**Arguments For:**
- Leverages xDSL's pass infrastructure
- Simpler initial construction
- Passes can be tested in isolation
- More "compiler-like" architecture

**Arguments Against:**
- **Violates verification invariants**: GraphIR's `ModuleOp.verify_()` assumes:
  - Endpoints reference valid instances
  - Endpoint uniqueness is enforced
  - An incomplete GraphIR would fail verification or require relaxed invariants.
- **Would need `elab_state` machinery**: Similar to what was explored with NFIR in ADR-0004.
- **Natural construction order is already correct**: Instances must exist before endpoints can reference them via `inst_id`.

### Current Flow (Already Optimal Order)
```python
# In lower_module():
inst_ops, inst_name_to_id, inst_names_by_ref, inst_error = lower_module_instances(...)
net_ops, port_order, net_error = lower_module_nets(..., inst_name_to_id=inst_name_to_id, ...)
```

Instances are lowered first, providing the `inst_name_to_id` mapping that net lowering needs.

### Verdict: ⚠️ Problematic

---

## Recommended Approach: Internal Decomposition

### Proposed Structure

```
src/asdl/ir/converters/ast_to_graphir/
├── __init__.py          # Public API: convert_document, convert_import_graph
├── context.py           # Session/document contexts (unchanged)
├── symbols.py           # Symbol resolution, ID allocation
├── patterns/
│   ├── __init__.py
│   ├── table.py         # PatternExpressionTable management
│   ├── axis.py          # _AxisToken, _AxisMetadata, _axis_* functions
│   └── broadcast.py     # _axis_broadcast_mapping, _axis_subsequence_positions
├── lowering/
│   ├── __init__.py
│   ├── instances.py     # lower_module_instances
│   ├── nets.py          # lower_module_nets (simplified)
│   └── devices.py       # lower_device, lower_backend
└── parsing.py           # Token parsing (unchanged)
```

### Key Changes

1. **Extract axis logic to `patterns/axis.py`**:
   - `_AxisToken`, `_AxisMetadata` dataclasses
   - `_collect_named_pattern_axes`
   - `_axis_metadata`
   - `_scan_group_tokens`
   - `_token_loc`

2. **Extract broadcast to `patterns/broadcast.py`**:
   - `_axis_subsequence_positions`
   - `_axis_broadcast_mapping`

3. **Simplify `lowering/nets.py`**:
   ```python
   def lower_module_nets(...):
       axis_context = collect_module_axes(module, diagnostics)
       
       for net_token, endpoint_expr in module.nets.items():
           net_atoms = atomize_net(net_token, axis_context, diagnostics)
           endpoint_bindings = resolve_endpoint_bindings(
               net_atoms, endpoint_expr, axis_context, inst_name_to_id, diagnostics
           )
           net_ops.extend(create_net_ops(net_atoms, endpoint_bindings, context))
       
       # Similar for instance_defaults
       ...
   ```

### Benefits

| Benefit | Description |
|---------|-------------|
| **Testable units** | Axis extraction and broadcast mapping can have dedicated unit tests |
| **No pipeline changes** | Keep AST→GraphIR→IFIR intact |
| **GraphIR invariants preserved** | Construction still produces valid IR |
| **Future extensibility** | If patterned parameters need axis logic, it's already extracted |
| **Clearer ownership** | Each module has single responsibility |

### Verdict: ✅ Recommended

---

## Summary Table

| Approach | Verdict | Rationale |
|----------|---------|-----------|
| Bring NFIR back | ❌ Not recommended | Relocates complexity, doesn't reduce it; violates ADR-0014 semantic ownership |
| Incomplete GraphIR + passes | ⚠️ Problematic | Violates verification invariants; would need `elab_state` machinery |
| Decompose converter internally | ✅ Recommended | Addresses actual pain point (monolithic function); preserves pipeline; testable |

---

## Follow-up Actions

If the internal decomposition approach is approved:

1. Create task card for extracting `patterns/` submodule
2. Create task card for simplifying `lowering/nets.py`
3. Add unit tests for axis metadata extraction in isolation
4. Add unit tests for broadcast mapping logic in isolation
5. Update `codebase_map.md` with new structure

---

## References

- ADR-0014: GraphIR Canonical Core
- ADR-0015: GraphIR Pattern Metadata
- ADR-0020: Tagged Pattern Axes Broadcast
- `docs/specs/spec_asdl_graphir.md`: GraphIR specification
