# ASDL Test Fixtures

This directory contains ASDL circuit files used for testing various features of the ASDL system.

## Available Fixtures

### `inverter.yml`
- **Purpose**: Basic CMOS inverter for fundamental parser and generator testing
- **Features**: Simple single-transistor instances, basic parameter handling
- **Use Cases**: Parser validation, SPICE generation, PySpice integration testing

### `diff_pair_nmos.yml` 
- **Purpose**: NMOS differential pair with resistor loads for pattern expansion testing
- **Features**: 
  - Pattern expansion in ports: `in_<p,n>` → `in_p`, `in_n`
  - Pattern expansion in instances: `MN_<P,N>` → `MN_P`, `MN_N`
  - Synchronized pattern mappings: `G<P,N>: in_<p,n>`
  - One-sided pattern mappings: `minus<P,N>: out_<p,n>`
  - Mixed instances (with and without patterns)
  - Complex PDK device lines with expressions
  - Parameter substitution with `$param` syntax
- **Use Cases**: Pattern expansion validation, pipeline integration testing

## Pattern Expansion Examples in `diff_pair_nmos.yml`

**Port Expansion**:
```yaml
in_<p,n>: {dir: in, type: voltage}  # → in_p, in_n
```

**Instance Name Expansion**:
```yaml
MN_<P,N>:  # → MN_P, MN_N (separate instances)
```

**Synchronized Mappings** (order-matched):
```yaml
G<P,N>: in_<p,n>  # → GP: in_p, GN: in_n
```

**One-sided Patterns**:
```yaml
plus: vdd           # → Both instances connect to vdd
minus<P,N>: out_<p,n>  # → minusP: out_p, minusN: out_n
```

**Expected Expansion Results**:
- `MN_P`: `{GP: in_p, DP: out_p, S: tail, B: vss}`
- `MN_N`: `{GN: in_n, DN: out_n, S: tail, B: vss}`
- `RL_P`: `{plus: vdd, minusP: out_p}`
- `RL_N`: `{plus: vdd, minusN: out_n}` 