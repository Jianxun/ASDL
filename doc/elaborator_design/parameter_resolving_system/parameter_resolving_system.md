# ASDL Parameter Resolving System

## Overview

The ASDL parameter resolving system provides a clean separation between external module interfaces and internal implementation details, while ensuring LVS (Layout vs Schematic) compatibility and maintaining simulation flexibility.

## Design Philosophy

### Core Principles

1. **Semantic Clarity**: Clear distinction between external interface and internal implementation
2. **LVS Compatibility**: Hierarchical modules generate fixed subcircuit definitions
3. **Device Flexibility**: Primitive devices maintain sizing flexibility where needed
4. **Simulation Control**: External parameter control through template-based approaches

## Field Definitions

### `parameters` (Canonical) / `params` (Abbreviation)

**Purpose**: External module interface - controllable parameters that define module behavior

**Characteristics**:
- **Overridable**: Can be overridden during instantiation (restricted to primitive modules only)
- **Design Intent**: "These are the knobs users can control"
- **LVS Impact**: Overrides create variations (restricted scope prevents LVS issues)
- **Usage**: Device dimensions (L, W, M), circuit specifications (frequency, gain)
- **Environment Variables**: Support `${VAR}` syntax for dynamic values from environment

### `variables` (Canonical) / `vars` (Abbreviation)

**Purpose**: Internal implementation constants and calculated values

**Characteristics**:
- **Non-overridable**: Cannot be overridden during instantiation
- **Design Intent**: "These are internal implementation details"
- **LVS Impact**: Always resolved to concrete values
- **Usage**: Model names, temperature coefficients, derived calculations, internal constants

## Environment Variable Support in Parameters

### Design Decisions

**Syntax**: Only `${VAR}` format is supported in parameter values
- **Valid**: `${PDK_ROOT}`, `${CORNER}`, `${TEMP}`
- **Invalid**: `$PDK_ROOT`, `${PDK_ROOT:-default}`, `${PDK_ROOT}/path`

**Resolution Timing**: Environment variables are resolved during elaboration phase, integrated with parameter resolution

**Error Handling**: 
- Missing environment variables emit `E0501` diagnostic with parameter context
- Invalid format emits error diagnostic for malformed syntax
- No default values - fail fast for missing environment variables

**Security**: No validation of environment variable names - let system handle malformed names naturally

### Implementation Approach

Environment variable resolution is integrated into the existing parameter resolution pipeline:

```python
class VariableResolver:
    def resolve_environment_variables(self, parameters: Dict) -> Dict:
        """Resolve ${VAR} syntax in parameter values."""
        # Resolve environment variables before parameter substitution
        # Emit E0501 for missing environment variables
        pass
    
    def resolve_instance_variables(self, instances, variables, module_name):
        """Existing method - now variables have environment variables resolved."""
        pass
```

### Usage Examples

```yaml
# Environment variables in parameters
nfet_03v3:
  parameters:
    L: "0.28u"
    W: "${WIDTH:-3u}"           # ❌ Invalid - no defaults supported
    M: "${MULTIPLIER}"          # ✅ Valid - uses $MULTIPLIER environment variable
    corner: "${CORNER}"          # ✅ Valid - uses $CORNER environment variable

# Template substitution works as before
spice_template: "MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M}"
```

### Diagnostic Messages

```
E0501: Environment variable ${PDK_ROOT} not found in parameter 'pdk_root'
E0502: Invalid environment variable format in parameter 'corner': expected ${VAR} format
```

### Error Codes

**E0501**: Environment Variable Not Found
- **When**: Environment variable referenced in parameter value is not defined
- **Message**: "Environment variable ${VAR_NAME} not found in parameter 'param_name'"
- **Severity**: ERROR
- **Resolution**: Set the required environment variable or use a static value

**E0502**: Invalid Environment Variable Format
- **When**: Parameter value contains malformed environment variable syntax
- **Message**: "Invalid environment variable format in parameter 'param_name': expected ${VAR} format"
- **Severity**: ERROR
- **Resolution**: Use correct `${VAR}` syntax in parameter value

### Implementation Workflow

#### Resolution Order
1. **Environment Variable Resolution**: Resolve `${VAR}` in parameter values
2. **Parameter Substitution**: Substitute resolved parameters in `spice_template`
3. **Template Generation**: Generate final SPICE with concrete values

#### Pipeline Integration
```
ASDL File → Parser → Elaborator (Environment Resolution + Parameter Resolution) → Generator → SPICE
```

The environment variable resolution happens during the elaboration phase, ensuring that:
- All environment variables are resolved to concrete values
- Parameter substitution works with existing generator logic
- No changes needed in template substitution mechanism

### Practical Example

#### Environment Setup
```bash
export PDK_ROOT=/usr/local/pdk/gf180mcu
export CORNER=fast
export TEMP=100
export WIDTH=6u
```

#### ASDL File
```yaml
nfet_03v3:
  parameters:
    L: "0.28u"
    W: "${WIDTH}"
    M: "${MULTIPLIER:-1}"  # ❌ Invalid - no defaults supported
    corner: "${CORNER}"
    temp: "${TEMP}"
  spice_template: "MN{name} {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M} corner={corner} temp={temp}"
```

#### Resolution Process
1. **Environment Resolution**: `${WIDTH}` → `"6u"`, `${CORNER}` → `"fast"`, `${TEMP}` → `"100"`
2. **Parameter Substitution**: `{W}` → `6u`, `{corner}` → `fast`, `{temp}` → `100`
3. **Final SPICE**: `MN... nfet_03v3 L=0.28u W=6u m=1 corner=fast temp=100`

#### Error Cases
- **Missing Environment Variable**: `${MULTIPLIER}` → `E0501: Environment variable ${MULTIPLIER} not found in parameter 'M'`
- **Invalid Format**: `$WIDTH` → `E0502: Invalid environment variable format in parameter 'W': expected ${VAR} format`

### Integration with Existing Systems

- **No changes to generator**: Environment variables are resolved to concrete values before template substitution
- **No changes to spice_template**: Uses existing `{param}` substitution mechanism
- **Clean separation**: Parameter resolution handles environment variables, generator handles template substitution

## Parameter Override Policy

### Design Rule: Primitives-Only Override

**Allowed**: Parameter overrides on primitive modules (with `spice_template`)
```yaml
MN:
  model: nfet_03v3  # primitive module
  parameters: {M: 2, W: "4u"}  # ✅ Override allowed - generates inline SPICE
```

**Forbidden**: Parameter overrides on hierarchical modules (with `instances`)
```yaml
INV1:
  model: inverter  # hierarchical module
  parameters: {nmos_M: 2}  # ❌ Forbidden - creates LVS issues
```

### Rationale

1. **Primitive modules** → Generate inline SPICE → No subcircuit definition issues
2. **Hierarchical modules** → Must have fixed parameters → LVS-compatible subcircuit definitions
3. **Device sizing flexibility** preserved where it matters most (primitive devices)
4. **Circuit topology stability** enforced (hierarchical modules have fixed behavior)

### LVS Compatibility

**Problem**: Hierarchical parameter overrides create parameterized subcircuits
```spice
.subckt inverter in out vdd vss
  .param nmos_M=1
  MNMN out in vss vss nfet_03v3 L=0.28u W=3u m={nmos_M}  # Parameterized
.ends

X_INV1 in out vdd vss inverter nmos_M=2  # Different parameter values
X_INV2 in out vdd vss inverter nmos_M=4  # Create LVS matching issues
```

**Solution**: Fixed subcircuit definitions with concrete values
```spice
.subckt inverter in out vdd vss
  MNMN out in vss vss nfet_03v3 L=0.28u W=3u m=1  # Concrete value
.ends

X_INV1 in out vdd vss inverter  # Fixed subcircuit
X_INV2 in out vdd vss inverter  # Identical calls
```

## Usage Examples

### Primitive Module Example

```yaml
nfet_03v3:
  doc: "GF180MCU NMOS transistor"
  ports:
    D: {dir: in_out, type: voltage}
    G: {dir: in, type: voltage}
    S: {dir: in_out, type: voltage}
    B: {dir: in_out, type: voltage}
  parameters:         # External interface - overridable
    L: "0.28u"
    W: "3u"
    M: 1
  variables:          # Internal constants - non-overridable
    model_name: "nfet_03v3"
    temp_coeff: "1.2e-3"
    process: "gf180mcu"
  spice_template: "MN{name} {D} {G} {S} {B} {model_name} L={L} W={W} m={M} tc={temp_coeff}"
  pdk: "gf180mcu"
```

### Hierarchical Module Example

```yaml
rc_filter:
  doc: "RC low-pass filter"
  ports:
    in: {dir: in, type: voltage}
    out: {dir: out, type: voltage}
    gnd: {dir: in, type: voltage}
  parameters:         # External interface (if needed)
    frequency: "1MHz"
  variables:          # Internal implementation details
    R_val: "10k"      # Calculated from frequency requirement
    C_val: "100p"     # Calculated from frequency requirement
  instances:
    R1:
      model: resistor
      mappings: {n1: in, n2: out}
      parameters: {R: "{R_val}"}  # Uses variable, not external parameter
    C1:
      model: capacitor
      mappings: {n1: out, n2: gnd}
      parameters: {C: "{C_val}"}  # Uses variable, not external parameter
```

### Instance Parameter Override (Primitives Only)

```yaml
test_circuit:
  instances:
    # ✅ Allowed: Override parameters on primitive modules
    FET1:
      model: nfet_03v3
      mappings: {D: drain, G: gate, S: source, B: bulk}
      parameters: {W: "6u", M: 2}  # Override W and M, L uses default
      # variables: {...}            # ❌ Cannot override variables
    
    # ❌ Forbidden: Override parameters on hierarchical modules
    # FILTER1:
    #   model: rc_filter
    #   parameters: {frequency: "10MHz"}  # Would be forbidden
    
    # ✅ Alternative: Use explicit variants for hierarchical modules
    FILTER1:
      model: rc_filter_10mhz  # Fixed variant with 10MHz design
```

## Template Substitution

Both `parameters` and `variables` are available in `spice_template` substitution:

```yaml
nfet_03v3:
  parameters: {L: "0.28u", W: "3u", M: 1}
  variables: {model_name: "nfet_03v3", temp_coeff: "1.2e-3"}
  spice_template: "MN{name} {D} {G} {S} {B} {model_name} L={L} W={W} m={M} tc={temp_coeff}"
  #                                          ^variable   ^param ^param ^param  ^variable
```

**Template Data Priority**: Variables can shadow parameters if same name exists (variables are more specific)

## Simulation Parameter Control

For simulation flexibility without breaking LVS compatibility, use **parameter hijacking**:

### Parameter Hijacking Strategy

1. **Parse normal ASDL** with concrete parameter values
2. **Simulator harness hijacks** parameter values in parsed object
3. **Replace with Jinja2 templates** before compilation
4. **ASDL compiler generates** template unknowingly
5. **Jinja2 renders** final simulation netlist

```python
# Step 1: Normal ASDL parsing
asdl_design = parser.parse_file("design.asdl")

# Step 2: Parameter hijacking for simulation
hijacker = ParameterHijacker()
sim_design = hijacker.hijack_parameters(asdl_design, {
    "nfet_03v3.W": "{{ transistor_width | default('3u') }}",
    "nfet_03v3.M": "{{ transistor_multiplier | default(1) }}"
})

# Step 3: Generate template SPICE
template_spice = generator.generate(sim_design)
# Result: MN... nfet_03v3 L=0.28u W={{ transistor_width | default('3u') }} m={{ transistor_multiplier | default(1) }}

# Step 4: Render final netlist
final_spice = jinja2.Template(template_spice).render({
    'transistor_width': '6u',
    'transistor_multiplier': 2
})
# Result: MN... nfet_03v3 L=0.28u W=6u m=2
```

## Field Name Conventions

### Canonical Names (Recommended for Documentation)
- **`parameters`** - Full clarity for formal documentation
- **`variables`** - Full clarity for formal documentation

### Permitted Abbreviations (Convenient for Daily Use)
- **`params`** - Alias for `parameters`
- **`vars`** - Alias for `variables`

### Style Examples

```yaml
# Style 1: Canonical (formal/documentation)
nfet_03v3:
  parameters: {L: "0.28u", W: "3u", M: 1}
  variables: {model_name: "nfet_03v3"}

# Style 2: Abbreviated (casual/compact)
nfet_03v3:
  params: {L: "0.28u", W: "3u", M: 1}
  vars: {model_name: "nfet_03v3"}

# Style 3: Mixed (practical)
nfet_03v3:
  params: {L: "0.28u", W: "3u", M: 1}      # Common usage - abbreviated
  variables: {model_name: "nfet_03v3"}     # Less common - canonical for clarity
```

## Implementation Guidelines

### Parser Implementation

```python
class Module:
    # Internal storage uses canonical names
    parameters: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_yaml(cls, data):
        # Accept both canonical and abbreviated forms
        params = data.get('parameters') or data.get('params')
        vars = data.get('variables') or data.get('vars')
        return cls(parameters=params, variables=vars)
```

### Validation Rules

```python
def validate_parameter_override(instance, target_module):
    """Validate parameter override rules."""
    if instance.parameters and target_module.instances is not None:
        # Hierarchical module with parameter override - forbidden
        raise ValidationError(
            f"Parameter overrides not allowed for hierarchical module '{instance.model}'. "
            f"Use primitive modules or create fixed variants instead."
        )
    
    if hasattr(instance, 'variables') and instance.variables:
        # Variable override attempts - always forbidden
        raise ValidationError(
            f"Variable overrides not allowed. Variables are internal implementation details."
        )
```

### Template Generation

```python
def generate_template_data(module, instance_overrides=None):
    """Generate template substitution data."""
    template_data = {}
    
    # Add module variables (internal constants)
    if module.variables:
        template_data.update(module.variables)
    
    # Add module parameters (with potential overrides)
    if module.parameters:
        params = module.parameters.copy()
        if instance_overrides and module.spice_template:
            # Only allow overrides for primitive modules
            params.update(instance_overrides)
        template_data.update(params)
    
    return template_data
```

## Migration Strategy

### From Current Mixed `parameters`

**Identify Usage Patterns**:
1. **Used in instance overrides** → Move to `parameters`
2. **Internal constants never overridden** → Move to `variables`
3. **Model names, coefficients** → Move to `variables`
4. **Device dimensions** → Keep in `parameters`

### Example Migration

```yaml
# Before: Mixed semantics
nfet_03v3:
  parameters:
    L: "0.28u"           # Used in overrides → parameters
    W: "3u"              # Used in overrides → parameters  
    M: 1                 # Used in overrides → parameters
    model_name: "nfet_03v3"  # Never overridden → variables
    temp_coeff: "1.2e-3"     # Never overridden → variables

# After: Clear semantics
nfet_03v3:
  parameters: {L: "0.28u", W: "3u", M: 1}
  variables: {model_name: "nfet_03v3", temp_coeff: "1.2e-3"}
```

## Benefits

### 1. Design Clarity
- **Clear semantic distinction** between external interface and internal implementation
- **Explicit design intent** about what can/cannot be controlled
- **Better modular design** with proper encapsulation

### 2. LVS Compatibility
- **Fixed subcircuit definitions** for hierarchical modules
- **Concrete parameter values** in generated SPICE
- **No parameterized subcircuits** that confuse LVS tools

### 3. Simulation Flexibility
- **Parameter hijacking** enables simulation control without breaking LVS
- **Template-based approach** leverages proven Jinja2 ecosystem
- **Hierarchical parameter access** with dot notation

### 4. Tool Integration
- **Industry standard patterns** that work with existing EDA tools
- **Clean separation** between design and simulation concerns
- **Backwards compatibility** through parser field aliasing

## Future Considerations

### Computed Variables
Support for calculated variables based on parameters:
```yaml
rc_filter:
  parameters: {frequency: "1MHz"}
  variables:
    R_val: "{{ 1 / (2 * pi * frequency * C_val) }}"  # Calculated from frequency
    C_val: "100p"
```

### Type System Integration
Parameters and variables could integrate with future type system:
```yaml
nfet_03v3:
  parameters:
    L: {type: length, value: "0.28u", min: "0.18u", max: "10u"}
    W: {type: length, value: "3u", min: "0.36u"}
    M: {type: integer, value: 1, min: 1, max: 1000}
  variables:
    model_name: {type: string, value: "nfet_03v3"}
```

### Parameter Dependencies
Support for parameter relationships and constraints:
```yaml
nfet_03v3:
  parameters: {L: "0.28u", W: "3u", M: 1}
  variables: {model_name: "nfet_03v3"}
  constraints:
    - "W >= 2 * L"  # Geometric constraint
    - "M * W <= 100u"  # Total width constraint
```

This parameter resolving system provides a robust foundation for both current needs and future enhancements while maintaining the core principles of clarity, LVS compatibility, and simulation flexibility.