# ASDL Style Guidelines

## Overview

This document defines style conventions and best practices for writing ASDL files, with a focus on symmetry representation, naming conventions, and circuit organization.

## Symmetry Representation Patterns

### 1. Differential Pair Symmetry

Use `<p,n>` suffix pattern for differential symmetry across ports, instances, and nets:

```yaml
# Ports: Use <p,n> suffix for differential signals
ports:
  vin_<p,n>: { dir: in, type: signal }

# Internal nets: Use <p,n> suffix for differential nodes
internal_nets:
  - vd_<p,n>  # Differential drain nodes

# Instances: Use <p,n> suffix for symmetric device arrays
instances:
  mn_in<p,n>:
    model: nmos
    mappings:
      D: vd_<p,n>      # Each device gets its corresponding net
      G: vin_<p,n>     # Each device gets its corresponding input
      S: tail           # Shared source connection
      B: vss            # Shared bulk connection
```

### 2. Instance Array Expansion

Instance arrays automatically expand into separate devices while maintaining synchronized mappings:

```yaml
# Single declaration expands to two instances: mn_inp and mn_inn
mn_in<p,n>:
  model: nmos
  mappings:
    D: <vd, vout>      # First item (vd) → first instance (p)
                       # Second item (vout) → second instance (n)
    G: vin_<p,n>       # Pattern expands: vin_p, vin_n
    S: tail             # Shared connection (no pattern)
```

### 3. Order-Synchronized Mappings

When using literal patterns in mappings, maintain consistent ordering:

```yaml
# Good: Standard differential connections
D: <vd, vout>          # p-side gets vd, n-side gets vout
G: vin_<p,n>           # p-side gets vin_p, n-side gets vin_n

# Good: Standard differential connections
D: <vd, vout>          # ✓ Clear: p-side to vd, n-side to vout
G: vin_<p,n>           # ✓ Clear: p-side to vin_p, n-side to vin_n

# Intentional: Cross-coupled connections for negative feedback
G: <vin_n, vin_p>      # p-side gets vin_n, n-side gets vin_p
                       # Creates cross-coupling for negative feedback
```

**Note**: Cross-coupled connections (order swapping) are intentional and valid for creating negative feedback loops, cross-coupled latches, and other circuit topologies where you want the p-side to respond to the n-side input and vice versa.

### 4. Shared vs. Differential Connections

- **Differential connections**: Use `<p,n>` patterns for nets that differ between sides
- **Shared connections**: Use single net names for connections common to both sides

```yaml
mappings:
  D: <vd, vout>        # Differential: p-side to vd, n-side to vout
  G: vin_<p,n>         # Differential: p-side to vin_p, n-side to vin_n
  S: tail               # Shared: both sides connect to tail
  B: vss                # Shared: both sides connect to vss
```

## Naming Conventions

### 1. Port Naming

- **Differential signals**: Use descriptive prefix + `<p,n>` suffix
  - `vin_<p,n>` for differential input
  - `vout_<p,n>` for differential output
  - `vcm_<p,n>` for common-mode signals

- **Single-ended signals**: Use descriptive names without patterns
  - `vdd`, `vss` for power supplies
  - `vbias` for bias voltages
  - `vref` for reference voltages

### 2. Instance Naming

- **Device arrays**: Use descriptive prefix + `<p,n>` suffix
  - `mn_in<p,n>` for NMOS input pair
  - `mp_load<p,n>` for PMOS load pair
  - `mn_tail<p,n>` for NMOS tail devices

- **Single devices**: Use descriptive names without patterns
  - `mn_bias` for bias reference
  - `mp_ref` for reference device

### 3. Net Naming

- **Differential nets**: Use descriptive prefix + `<p,n>` suffix
  - `vd_<p,n>` for differential drain nodes
  - `vg_<p,n>` for differential gate nodes

- **Shared nets**: Use descriptive names without patterns
  - `tail` for tail current node
  - `vref` for reference voltage node

## Circuit Organization

### 1. Module Structure

Organize modules in logical sections:

```yaml
modules:
  ota_5t:
    ports:
      # Input/output ports first
      vin_<p,n>: { dir: in, type: signal }
      vout: { dir: out, type: signal }
      
      # Power and bias ports
      vdd: { dir: in, type: power }
      vss: { dir: in, type: ground }
      vbias: { dir: in, type: bias }
    
    internal_nets:
      # List internal nodes with descriptive names
      - tail
      - vd_<p,n>
    
    instances:
      # Group by function with clear comments
      # Current mirror load
      mp_load<p,n>: ...
      
      # Differential input pair
      mn_in<p,n>: ...
      
      # Bias and tail devices
      mn_bias: ...
      mn_tail: ...
```

### 2. Instance Grouping

Group related instances together with clear section comments:

```yaml
instances:
  # PMOS current mirror load
  mp_ref: ...
  mp_load: ...
  
  # NMOS differential pair
  mn_inp: ...
  mn_inn: ...
  
  # Bias and current sources
  mn_bias: ...
  mn_tail: ...
```

### 3. Parameter Organization

Group related parameters logically:

```yaml
parameters:
  # Device sizing
  L: 0.28u
  W: 3u
  
  # Multiplier factors
  m: 2
  
  # Temperature and process
  temp: 27
  process: "tt"
```

## Best Practices

### 1. Pattern Usage

- **Use patterns for symmetry**: Always use `<p,n>` for differential circuits
- **Keep patterns simple**: Avoid complex nested patterns
- **Document pattern intent**: Use comments to explain pattern relationships

### 2. Error Prevention

- **Validate pattern counts**: Ensure pattern items match between related mappings
- **Test expansion**: Verify that patterns expand to expected results
- **Use consistent ordering**: Maintain consistent `<p,n>` ordering throughout

### 3. Readability

- **Clear naming**: Use descriptive names that explain device function
- **Logical grouping**: Organize instances by functional blocks
- **Helpful comments**: Add comments explaining circuit intent and relationships

## Examples

### Complete Differential Pair

```yaml
modules:
  diff_pair:
    ports:
      vin_<p,n>: { dir: in, type: signal }
      vout_<p,n>: { dir: out, type: signal }
      vdd: { dir: in, type: power }
      vss: { dir: in, type: ground }
      vbias: { dir: in, type: bias }
    
    internal_nets:
      - tail
    
    instances:
      # Input differential pair
      mn_in<p,n>:
        model: nmos
        mappings:
          D: vout_<p,n>
          G: vin_<p,n>
          S: tail
          B: vss
        parameters:
          m: 1
      
      # Tail current source
      mn_tail:
        model: nmos
        mappings:
          D: tail
          G: vbias
          S: vss
          B: vss
        parameters:
          m: 2
```

### Current Mirror

```yaml
# Current mirror with diode reference
mp_mirror<p,n>:
  model: pmos
  mappings:
    D: <vref, vout>    # p-side diode, n-side output
    G: vref             # Both gates to reference
    S: vdd              # Both sources to supply
    B: vdd              # Both bulks to supply
  parameters:
    m: 1
```

## Summary

The key principles for ASDL symmetry representation are:

1. **Use `<p,n>` suffix consistently** for differential symmetry
2. **Leverage instance arrays** to avoid duplication
3. **Maintain synchronized ordering** in pattern mappings
4. **Separate shared vs. differential** connections clearly
5. **Use descriptive naming** that explains circuit function
6. **Organize logically** by functional blocks
7. **Document intent** with clear comments

Following these guidelines ensures that ASDL files are readable, maintainable, and correctly represent circuit symmetry.
