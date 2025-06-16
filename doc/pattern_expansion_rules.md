# ASDL Pattern Expansion Rules

## Overview

ASDL supports pattern expansion to generate multiple similar circuit elements from concise pattern syntax. This document defines the rules for literal expansion using `<>` patterns.

## Literal Expansion with `<>`

The literal expansion applies to nets, ports, mappings, and instance names using angle bracket syntax.

### Basic Syntax

```
<item1,item2,...,itemN>
```

- **Minimum items**: N ≥ 2 (at least two items required)
- **Non-empty requirement**: At least one item must be non-empty
- **Whitespace handling**: All whitespace around items is removed
- **No escape sequences**: Special characters not supported to avoid ngspice confusion

### Simple Examples

#### Differential Signal Expansion
```yaml
# Input
port: in_<p,n>

# Output  
ports:
  - in_p
  - in_n
```

#### Empty Suffix Support
```yaml
# Input
signal: clk<,b>

# Output
signals:
  - clk      # First item is empty string
  - clkb
```

#### No Prefix Expansion
```yaml
# Input
signals: <ab,cd>

# Output
signals:
  - ab
  - cd
```

## Order-Sensitive Expansion

When both sides of a mapping contain patterns, they expand in synchronized order:

```yaml
# Input
mappings:
  port_<p,n>: net_<n,p>

# Output
mappings:
  port_p: net_n    # 1st left item → 1st right item
  port_n: net_p    # 2nd left item → 2nd right item
```

## One-Sided Patterns

When only one side of a mapping contains a pattern, it expands to connect multiple ports/instances to the same net:

```yaml
# Input
mappings:
  data_<p,n>: vdd

# Output
mappings:
  data_p: vdd
  data_n: vdd
```

**Note**: This creates multiple ports connecting to the same net, which is legal. However, mapping a single port to multiple nets is illegal as it creates implicit shorts.

## Instance Expansion

### Basic Instance Expansion

```yaml
# Input
instances:
  M_<P,N>:
    model: nmos_unit
    mappings:
      G: gate
      D: drain_<P,N>

# Output
instances:
  M_P:
    model: nmos_unit
    mappings:
      G: gate
      D: drain_P
      
  M_N:
    model: nmos_unit
    mappings:
      G: gate  
      D: drain_N
```

### Synchronized Instance and Port Patterns

When instance names have patterns, port mappings must use exactly the same pattern to maintain clear instance boundaries:

```yaml
# Input
instances:
  M_<P,N>:
    model: nmos_unit
    mappings:
      port_a<P,N>: net_x_<p,n>  # Must match instance pattern
      port_b<P,N>: net_y        # One-sided patterns OK

# Output
instances:
  M_P:
    model: nmos_unit
    mappings:
      port_aP: net_x_p
      port_bP: net_y
      
  M_N:
    model: nmos_unit
    mappings:
      port_aN: net_x_n
      port_bN: net_y
```

**Important**: Each expanded instance gets its own separate instantiation block with its own mappings. Mappings from different expanded instances are never merged together.

## Error Conditions

The following patterns will throw exceptions:

### Mismatched Item Counts
```yaml
# ERROR: 2 items vs 3 items
mappings:
  port_<p,n>: net_<a,b,c>
```

### Empty or Invalid Patterns
```yaml
# ERROR: Empty pattern
signal_<>

# ERROR: Single item (minimum 2 required)
port_<p>

# ERROR: All items empty (at least 1 non-empty required)
net_<,>
```

### Circuit Integrity Violations
```yaml
# ERROR: One port mapping to multiple nets creates shorts
# This would be caught during expansion validation
```

## Legal Circuit Patterns

### Many-to-One Connections (Legal)
```yaml
# Multiple ports connecting to same net - Legal
mappings:
  port_p: vdd
  port_n: vdd
```

### One-to-Many Connections (Illegal)  
```yaml
# Single port connecting to multiple nets - Creates shorts
# This pattern is prevented by expansion rules
```

## Future Extensions

### Array Expansion with `[]` (Not in MVP)
```yaml
# Future feature - not implemented in MVP
data_<p,n>[3:0]  # Would create: data_p[3], data_p[2], ..., data_n[0]
```

### Multiple Patterns (Discouraged)
```yaml
# Strongly discouraged - complex and error-prone
signal_<p,n>_<in,out>  # Would create 4 combinations
```

## Implementation Notes

- **Parse order**: Extract patterns, validate syntax, then expand
- **Validation**: Check item counts and emptiness before expansion
- **Integration**: Expansion occurs after parsing, before SPICE generation
- **Error handling**: Throw exceptions for invalid patterns with clear error messages
- **Testing**: Comprehensive test coverage for all valid patterns and error conditions

## Examples for Testing

### Valid Expansions
```yaml
# Differential pairs
in_<p,n> → [in_p, in_n]

# Clock generation  
clk<,b> → [clk, clkb]

# Cross-connections
{port_<p,n>: net_<n,p>} → {port_p: net_n, port_n: net_p}

# Instance arrays
M_<A,B> with port_<A,B> → separate M_A and M_B instances
```

### Error Cases
```yaml
# All should throw exceptions
port_<p,n>: net_<a,b,c>  # Mismatched counts
signal_<>                # Empty pattern  
port_<p>                 # Single item
net_<,>                  # All empty items
``` 