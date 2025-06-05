# Project Memory

## Project Overview
ASDL (Analog Structured Description Language) is a YAML-based representation for analog circuits that serves as an intermediate format between human-readable schematics and machine-friendly netlists. The goal is to create a hierarchical YAML-to-SPICE converter that preserves design intent and supports pattern expansion for AI/ML training datasets.

The objective is to develop a plain text intermediate representation that:
- Is more human-friendly than raw netlists but more machine-processable than schematics
- Carries topological information AND structural/design intent
- Can be used to curate datasets for training AI models for analog circuit design
- Serves as a bridge between design tools and AI systems

## Current State
**Phase 1 Complete:** Basic YAML parser with comprehensive data models and testing.

**Phase 1.5 Critical Discovery:** Found and resolved major syntax ambiguity in ASDL format regarding device pin connections vs parameters.

**ASDL Syntax Migration Complete:** Successfully migrated from confusing `.defaults` anchor syntax to intuitive `models` section for defining physical devices.

**Parser Refactoring Complete:** Refactored parser class with simplified, cleaner API enforcing strict dictionary format for circuits.

**JSON Export Feature:** Added debugging capability to dump parsed structures to JSON for manual inspection and troubleshooting.

**Ready for Phase 2:** Pattern expansion system implementation.

## Key Decisions

### Parser Architecture (Phase 1)
- **Data Models:** Simple dataclasses (`ASDLFile`, `ASDLModule`, `Circuit`) for prototype agility
- **Error Handling:** Custom `ASDLParseError` with context for debugging
- **YAML Processing:** Using `yaml.FullLoader` to handle anchors/aliases and complex expressions
- **Testing Strategy:** Comprehensive test suite with both unit tests and integration testing

### ASDL Syntax Migration (Phase 1.6 - Complete)
**MAJOR SYNTAX CHANGE:** Replaced confusing `.defaults` anchor syntax with clear `models` section:

**OLD SYNTAX (Confusing):**
```yaml
.defaults: &DEF
  NMOS: &NMOS {model: nmos_unit, B: VSS}
  PMOS: &PMOS {model: pmos_unit, B: VDD}

circuits:
  - {<<: *NMOS, name: MN1, nets: {S: vss, D: out, G: in}, M: 4}
```

**NEW SYNTAX (Intuitive):**
```yaml
models:
  nmos_unit: {model: nfet_3v3, L: 0.18u, W: 2u, NF: 2}
  pmos_unit: {model: pfet_3v3, L: 0.18u, W: 4u, NF: 2}

circuits:
  - name: MN1
    model: nmos_unit
    nets: {S: vss, D: out, G: in, B: VSS}
    M: 4
```

**Benefits:**
- Eliminated confusing YAML anchor syntax (`&`, `*`, `<<:`)
- Physical device models defined clearly in dedicated `models` section
- Device instantiation uses direct model names instead of anchor references
- Better separation of concerns: models vs instances
- More intuitive for users unfamiliar with YAML anchors

### ASDL Syntax Standards (Phase 1.5 - Critical)
**EXPLICIT SYNTAX:** Separation of device pin connections from parameters:
```yaml
# CORRECT (final standard):
- name: MN1
  model: nmos_unit
  nets: {S: vss, D: out, G: in, B: VSS}  # Pin connections (explicit bulk)
  M: 4, W: "10u", L: "180n"              # Device parameters
```

**Impact:**
- Device pin connections (S, D, G, B) explicitly declared in `nets` field
- Device parameters (M, W, L, VALUE) remain as top-level parameters  
- Hierarchical module connections already used correct `nets:` syntax
- **Explicit bulk connections:** All bulk terminals explicitly declared for transparency
- **Simple model definitions:** Models contain only device information for clarity

### JSON Export Feature (Phase 1.5)
- **Methods Added:** `to_dict()`, `to_json()`, `save_json()`, `print_summary()`
- **Parser Enhancement:** `parse_and_dump()` method for immediate debugging
- **Use Cases:** Manual inspection, debugging pattern expansion, validating parameter resolution, comparing transformations

### Parser Refactoring (Phase 1.7 - Complete)
**MAJOR API SIMPLIFICATION:** Refactored parser class for cleaner, more consistent operation:

**Key Changes:**
1. **Removed `parse_file` method** - Users are now responsible for reading files into strings
2. **Removed `parse_and_dump` method** - Parsing and dumping are now independent operations
3. **Enforced dictionary format for circuits** - All circuit instantiations must have unique names
4. **Removed YAML merge key support** - No more `<<:` anchor merging in circuit definitions
5. **Removed special jumper handling** - Jumpers are now defined in the `models` section like other components

**Benefits:**
- Cleaner separation of concerns (file I/O vs parsing)
- Enforced unique circuit names prevent naming conflicts
- Simplified parser logic by removing special cases
- More consistent syntax without YAML anchor complexity
- Better error handling for duplicate names

**Example of new strict syntax:**
```yaml
models:
  jumper: {model: jumper}
  nmos_unit: {model: nfet_3v3, L: 0.18u, W: 2u}

modules:
  bias_gen:
    circuits:
      MN1:  # Dictionary key becomes circuit name
        model: nmos_unit
        nets: {S: vss, D: out, G: in, B: VSS}
      J1:   # Jumper defined like any other component
        model: jumper
        nets: {p1: in, p2: out}
```

## Technical Architecture

### Data Flow
```
YAML Input → Parser → Data Models → [Pattern Expander] → [Parameter Resolver] → SPICE Generator
```

### File Structure
```
src/asdl/
  ├── models.py      # Data structures (ASDLFile with models field, ASDLModule, Circuit)
  ├── parser.py      # YAML parsing with models section support
  └── __init__.py    # Package exports
tests/
  └── test_parser.py # Comprehensive parser tests (10/10 passing)
examples/
  ├── ota_two_stg.yaml              # Original (legacy .defaults syntax)  
  ├── ota_two_stg_fixed.yaml        # New (models section + explicit nets)
  ├── ota_two_stg_parsed.json       # Debug output (original)
  └── ota_two_stg_fixed_parsed.json # Debug output (fixed)
```

### Dependencies
- **Core:** PyYAML (YAML parsing), pytest (testing)
- **Development:** black, flake8 (code quality)
- **Optional:** numpy, matplotlib (future analysis features)

## Open Questions

### ASDL Format Standardization
1. **Legacy Support:** Should we maintain backward compatibility with `.defaults` syntax temporarily?
2. **Migration Tools:** Should we create automated conversion tools for existing ASDL files?
3. **Validation:** Should we add strict schema validation to catch syntax issues early?

### Pattern Expansion (Phase 2)
1. **Expansion Strategy:** How to handle nested patterns like `"MN_{P,N}_{1,2}"` → `MN_P_1, MN_P_2, MN_N_1, MN_N_2`?
2. **Net Mapping:** How to align pattern expansions in names with pattern expansions in nets?
3. **Error Handling:** How to detect and report pattern mismatches?

### Parameter Resolution (Phase 3)  
1. **Expression Evaluation:** Support for mathematical expressions in `${...}` substitutions?
2. **Scope Rules:** How to handle parameter shadowing in nested modules?
3. **Type System:** Should parameters be typed (voltage, current, length, etc.)?

## Implementation Notes

### YAML Syntax Constraints
- Pattern keys must be quoted: `"in_{p,n}": in`
- Parameter substitutions must be quoted: `M: "${M.diff}"`
- Complex patterns must be quoted: `"out_{p,n}": "{n_d, out}"`
- Model names are simple identifiers (no quotes needed)

### Testing Strategy
- **Unit Tests:** Individual parser components with edge cases
- **Integration Tests:** Complete OTA file parsing with 6 modules  
- **Error Tests:** Invalid YAML, missing files, malformed structure
- **Migration Tests:** Both old (.defaults) and new (models) syntax support
- **Debug Tests:** JSON export functionality validation

### Performance Considerations
- Current focus: correctness and agility over performance
- Dataclasses provide simplicity for prototype development
- YAML parsing is the likely bottleneck for large files
- Pattern expansion will be the next performance consideration

## Project Structure Established
```
ASDL/
├── README.md              # Project overview and documentation
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore patterns
├── context/              # Project context tracking
├── src/asdl/             # Main source code (models section support)
├── tests/                # Test suite directory (10/10 passing)
├── examples/             # Example ASDL circuits (old and new syntax)
├── doc/                  # Documentation and syntax guides
└── dataset/              # Circuit dataset for AI training
``` 