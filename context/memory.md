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

**JSON Export Feature:** Added debugging capability to dump parsed structures to JSON for manual inspection and troubleshooting.

**Ready for Phase 2:** Pattern expansion system implementation.

## Key Decisions

### Parser Architecture (Phase 1)
- **Data Models:** Simple dataclasses (`ASDLFile`, `ASDLModule`, `Circuit`) for prototype agility
- **Error Handling:** Custom `ASDLParseError` with context for debugging
- **YAML Processing:** Using `yaml.FullLoader` to handle anchors/aliases and complex expressions
- **Testing Strategy:** Comprehensive test suite with both unit tests and integration testing

### ASDL Syntax Standards (Phase 1.5 - Critical)
**MAJOR ISSUE DISCOVERED:** Original ASDL syntax mixed device pin connections with parameters:
```yaml
# PROBLEMATIC (original):
- {<<: *NMOS, name: MN1, S: vss, D: out, G: in, M: 4}  # S,D,G treated as parameters
```

**SOLUTION IMPLEMENTED:** Explicit separation using `nets:` field:
```yaml
# CORRECT (final standard):
- {<<: *NMOS, name: MN1, 
   nets: {S: vss, D: out, G: in, B: VSS},  # Pin connections (explicit bulk)
   M: 4, W: "10u", L: "180n"}              # Device parameters
```

**ANCHOR STANDARD:** Clean anchors contain only device model information:
```yaml
# RECOMMENDED anchors:
NMOS: &NMOS {model: nmos_unit}     # Model only, no pins
PMOS: &PMOS {model: pmos_unit}     # Model only, no pins
```

**Impact:**
- Device pin connections (S, D, G, B) explicitly declared in `nets` field
- Device parameters (M, W, L, VALUE) remain as top-level parameters  
- Hierarchical module connections already used correct `nets:` syntax
- Updated ASDL schema documentation with explicit pin declaration examples
- **Explicit bulk connections:** All bulk terminals explicitly declared for transparency
- **Simple anchors:** Anchors contain only model information for clarity

### JSON Export Feature (Phase 1.5)
- **Methods Added:** `to_dict()`, `to_json()`, `save_json()`, `print_summary()`
- **Parser Enhancement:** `parse_and_dump()` method for immediate debugging
- **Use Cases:** Manual inspection, debugging pattern expansion, validating parameter resolution, comparing transformations

## Technical Architecture

### Data Flow
```
YAML Input → Parser → Data Models → [Pattern Expander] → [Parameter Resolver] → SPICE Generator
```

### File Structure
```
src/asdl/
  ├── models.py      # Data structures (ASDLFile, ASDLModule, Circuit)
  ├── parser.py      # YAML parsing with error handling
  └── __init__.py    # Package exports
tests/
  └── test_parser.py # Comprehensive parser tests (9/9 passing)
examples/
  ├── ota_two_stg.yaml              # Original (problematic syntax)  
  ├── ota_two_stg_fixed.yaml        # Fixed (proper nets/parameters)
  ├── ota_two_stg_parsed.json       # Debug output (original)
  └── ota_two_stg_fixed_parsed.json # Debug output (fixed)
```

### Dependencies
- **Core:** PyYAML (YAML parsing with anchors), pytest (testing)
- **Development:** black, flake8 (code quality)
- **Optional:** numpy, matplotlib (future analysis features)

## Open Questions

### ASDL Format Standardization
1. **Syntax Migration:** Should we update all existing ASDL files to use explicit `nets:` syntax?
2. **Backward Compatibility:** Should the parser support both old and new syntax temporarily?
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
- YAML anchors work correctly with `FullLoader`

### Testing Strategy
- **Unit Tests:** Individual parser components with edge cases
- **Integration Tests:** Complete OTA file parsing with 6 modules  
- **Error Tests:** Invalid YAML, missing files, malformed structure
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
├── src/asdl/             # Main source code (ready for implementation)
├── tests/                # Test suite directory
├── examples/             # Example ASDL circuits
├── doc/                  # Documentation and syntax guides
└── dataset/              # Circuit dataset for AI training
``` 