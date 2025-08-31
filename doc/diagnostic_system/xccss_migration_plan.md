# XCCSS Migration Implementation Plan

This document outlines the detailed implementation plan for migrating from the current `PXXX` diagnostic system to the new XCCSS format (`XCCSS`).

## Migration Overview

The migration will be executed in 5 phases to minimize disruption and allow for thorough testing at each stage:

1. **Phase 1: Foundation** - Create new diagnostic infrastructure
2. **Phase 2: Parser Migration** - Migrate parser diagnostics as proof-of-concept
3. **Phase 3: Component Migration** - Migrate remaining components
4. **Phase 4: Tool Updates** - Update external tools and documentation
5. **Phase 5: Cleanup** - Remove legacy system and finalize migration

## Phase 1: Foundation (Week 1-2)

### Deliverables

1. **Core Diagnostic Infrastructure**
   - `src/asdl/diagnostics/diagnostic.py` - Enhanced Diagnostic class
   - `src/asdl/diagnostics/registry.py` - Central registry
   - `src/asdl/diagnostics/__init__.py` - Public API exports

2. **Testing Infrastructure**
   - `tests/unit_tests/diagnostics/test_registry.py` - Registry validation tests
   - `tests/unit_tests/diagnostics/test_diagnostic.py` - Diagnostic creation tests
   - CI integration for conflict detection

3. **Development Tools**
   - `tools/validate_diagnostics.py` - Manual validation script
   - `tools/generate_diagnostic_docs.py` - Documentation generator

### Implementation Tasks

#### Task 1.1: Enhanced Diagnostic Class
```python
# src/asdl/diagnostics/diagnostic.py
@dataclass
class Diagnostic:
    # Existing fields...
    
    @classmethod
    def create(cls, code: str, location: Optional[Locatable] = None, **kwargs) -> 'Diagnostic':
        """Create diagnostic with XCCSS template processing"""
        # Implementation with template substitution and severity detection
    
    @staticmethod
    def _detect_severity(code: str) -> DiagnosticSeverity:
        """Auto-detect severity from XCCSS category code"""
        # Implementation based on category ranges
```

#### Task 1.2: Central Registry
```python
# src/asdl/diagnostics/registry.py
class DiagnosticRegistry:
    _all_diagnostics: Dict[str, Tuple[str, str]] = {}
    
    @classmethod
    def register_component_diagnostics(cls, diagnostics: Dict[str, Tuple[str, str]]):
        """Register diagnostics from a component"""
    
    @classmethod
    def validate_no_conflicts(cls) -> List[str]:
        """Validate no duplicate codes across all components"""
```

#### Task 1.3: Registry Validation Tests
```python
# tests/unit_tests/diagnostics/test_registry.py
def test_no_duplicate_codes():
    """Ensure no diagnostic codes conflict across components"""
    
def test_xccss_format_validation():
    """Validate all codes follow XCCSS format"""
    
def test_category_severity_consistency():
    """Ensure category codes map to correct severities"""
```

## Phase 2: Parser Migration (Week 3)

### Deliverables

1. **Parser Diagnostic Definitions**
   - `src/asdl/parser/diagnostics.py` - PARSER_DIAGNOSTICS and helper class
   
2. **Parser Integration**
   - Update `src/asdl/parser.py` to use new diagnostic system
   - Maintain backward compatibility with existing error codes

3. **Migration Testing**
   - Comprehensive tests for all parser diagnostics
   - Backward compatibility validation

### Code Mapping

| Legacy Code | New Code | Category | Title |
|-------------|----------|----------|-------|
| P100 | P0101 | Syntax | Invalid YAML Syntax |
| P101 | P0102 | Syntax | Invalid Root Type |
| P102 | P0201 | Schema | Missing Required Section |
| P103 | P0202 | Schema | Invalid Section Type |
| P104 | P0203 | Schema | Missing Required Field |
| P105 | P0301 | Semantic | Port Parsing Error |
| P106 | P0302 | Semantic | Invalid Import Format |
| P107 | P0303 | Semantic | Module Type Conflict |
| P108 | P0304 | Semantic | Incomplete Module Definition |
| P200 | P0701 | Extension | Unknown Top-Level Section |
| P201 | P0702 | Extension | Unknown Field |
| P301 | P0601 | Style | Dual Parameter Syntax |
| P302 | P0602 | Style | Dual Variables Syntax |

### Implementation Tasks

#### Task 2.1: Parser Diagnostic Definitions
```python
# src/asdl/parser/diagnostics.py
PARSER_DIAGNOSTICS = {
    # Syntax errors (P01xx)
    "P0101": ("Invalid YAML Syntax", "The file could not be parsed because of a syntax error: {error}"),
    "P0102": ("Invalid Root Type", "The root of an ASDL file must be a dictionary (a set of key-value pairs)."),
    
    # Schema errors (P02xx) 
    "P0201": ("Missing Required Section", "'{section}' is a mandatory section and must be present at the top level."),
    "P0202": ("Invalid Section Type", "The '{section}' section must be a dictionary (mapping), but found {type}."),
    "P0203": ("Missing Required Field", "{context} is missing the required '{field}' field."),
    
    # Semantic errors (P03xx)
    "P0301": ("Port Parsing Error", "An error occurred while parsing {context}: {error}"),
    "P0302": ("Invalid Import Format", "Import '{alias}' has invalid format. Expected 'library.filename[@version]'."),
    "P0303": ("Module Type Conflict", "Module '{module}' cannot have both 'spice_template' and 'instances'."),
    "P0304": ("Incomplete Module Definition", "Module '{module}' must have either 'spice_template' or 'instances'."),
    
    # Style warnings (P06xx)
    "P0601": ("Dual Parameter Syntax", "{context} contains both 'parameters' and 'params' fields."),
    "P0602": ("Dual Variables Syntax", "{context} contains both 'variables' and 'vars' fields."),
    
    # Extension warnings (P07xx)
    "P0701": ("Unknown Top-Level Section", "The top-level section '{section}' is not a recognized ASDL section."),
    "P0702": ("Unknown Field", "{context} contains unknown field '{field}' which is not recognized."),
}

class ParserDiagnostics:
    """Helper class for creating parser diagnostics with type safety"""
    
    @staticmethod
    def invalid_yaml_syntax(error: str, location: Locatable) -> Diagnostic:
        return Diagnostic.create("P0101", location=location, error=error)
    
    @staticmethod
    def missing_required_section(section: str, location: Locatable) -> Diagnostic:
        return Diagnostic.create("P0201", location=location, section=section)
    
    # ... additional helper methods for all parser diagnostics
```

#### Task 2.2: Parser Integration
```python
# src/asdl/parser.py (updated sections)
from .parser.diagnostics import ParserDiagnostics

class ASDLParser:
    def parse_string(self, yaml_content: str, file_path: Optional[Path] = None):
        # Replace existing diagnostic creation:
        # OLD: diagnostics.append(Diagnostic(code="P100", title="...", details="..."))
        # NEW: diagnostics.append(ParserDiagnostics.invalid_yaml_syntax(str(e.problem), loc))
```

#### Task 2.3: Backward Compatibility Layer
```python
# src/asdl/diagnostics/compatibility.py
LEGACY_CODE_MAPPING = {
    "P100": "P0101", "P101": "P0102", "P102": "P0201",
    # ... complete mapping
}

class LegacyDiagnosticAdapter:
    @staticmethod
    def convert_legacy_code(old_code: str) -> str:
        return LEGACY_CODE_MAPPING.get(old_code, old_code)
    
    @staticmethod
    def is_legacy_code(code: str) -> bool:
        return code in LEGACY_CODE_MAPPING
```

## Phase 3: Component Migration (Week 4-5)

### Phase 3.1: Elaborator Migration

#### Deliverables
- `src/asdl/elaborator/diagnostics.py` - Elaborator diagnostic definitions
- Updated elaborator to use new diagnostic system
- Comprehensive tests for elaborator diagnostics

#### New Diagnostic Codes
```python
ELABORATOR_DIAGNOSTICS = {
    # Syntax errors (E01xx)
    "E0101": ("Empty Pattern", "A literal pattern <> cannot be empty. It must contain items to expand."),
    "E0102": ("Single-Item Pattern", "A literal pattern must contain at least two items to be meaningful."),
    "E0103": ("Invalid Bus Range", "Bus range [{range}] is invalid or malformed."),
    
    # Semantic errors (E03xx)
    "E0301": ("Pattern Count Mismatch", "Pattern item count mismatch: {source} has {source_count} items, {target} has {target_count} items."),
    "E0302": ("Mixed Pattern Types", "Name '{name}' cannot contain both literal pattern <> and bus pattern []."),
    "E0303": ("Empty Pattern Item", "All items in pattern '{pattern}' are empty strings."),
    
    # Reference errors (E04xx)
    "E0401": ("Undefined Parameter", "Parameter '{parameter}' is referenced but not defined in {context}."),
    "E0402": ("Malformed Parameter Expression", "Parameter expression '{expression}' is malformed: {error}."),
}
```

### Phase 3.2: Validator Migration

#### Deliverables
- `src/asdl/validator/diagnostics.py` - Validator diagnostic definitions  
- Updated validator to use new diagnostic system
- Comprehensive tests for validator diagnostics

#### New Diagnostic Codes
```python
VALIDATOR_DIAGNOSTICS = {
    # Reference errors (V04xx)
    "V0401": ("Undefined Module", "Module '{module}' is referenced but not defined."),
    "V0402": ("Undefined Model", "Model '{model}' is referenced in instance '{instance}' but not defined."),
    "V0403": ("Circular Module Dependency", "Circular dependency detected in module hierarchy: {cycle}."),
    "V0404": ("Duplicate Definition", "Duplicate definition of '{name}' found in {context}."),
    "V0405": ("Invalid Port Connection", "Port connection '{connection}' is invalid: {reason}."),
    
    # Style warnings (V06xx)
    "V0601": ("Unused Module", "Module '{module}' is defined but never used."),
    "V0602": ("Unused Port", "Port '{port}' is declared but never connected."),
    "V0603": ("Undeclared Net Usage", "Net '{net}' is used but not declared as port or internal_net."),
    "V0604": ("Floating Input Port", "Input port '{port}' is not connected to any net."),
}
```

### Phase 3.3: Generator Migration

#### Deliverables
- `src/asdl/generator/diagnostics.py` - Generator diagnostic definitions
- Updated generator to use new diagnostic system
- Tests for generator diagnostics

#### New Diagnostic Codes
```python
GENERATOR_DIAGNOSTICS = {
    # Semantic errors (G03xx)
    "G0301": ("Cannot Generate SPICE", "Cannot generate SPICE for incomplete module '{module}'."),
    "G0302": ("Missing PDK Reference", "Primitive module '{module}' missing PDK reference for SPICE generation."),
    
    # Type errors (G05xx)
    "G0501": ("Unsupported Output Format", "Output format '{format}' is not supported by the generator."),
    "G0502": ("Template Processing Error", "Error processing SPICE template: {error}."),
}
```

## Phase 4: Tool Updates (Week 6)

### Deliverables

1. **CLI Tools Update**
   - Update compiler CLI to handle new diagnostic codes
   - Update linter CLI to handle new diagnostic codes
   - Maintain backward compatibility for existing scripts

2. **Documentation Update**
   - Generate new diagnostic documentation from registry
   - Update migration guide with code mappings
   - Update user-facing documentation

3. **External Tool Support**
   - Update any external tools that depend on diagnostic codes
   - Provide migration utilities for third-party tools

### Implementation Tasks

#### Task 4.1: Auto-Generated Documentation
```python
# tools/generate_diagnostic_docs.py
def generate_diagnostic_documentation():
    """Generate markdown documentation from diagnostic registry"""
    
    output = "# ASDL Diagnostic Codes (XCCSS Format)\n\n"
    
    for component in ["Parser", "Elaborator", "Validator", "Generator"]:
        diagnostics = DiagnosticRegistry.get_codes_by_component(component[0])
        output += f"## {component} Diagnostics\n\n"
        
        for code in sorted(diagnostics):
            title, template = DiagnosticRegistry.get_diagnostic_info(code)
            severity = Diagnostic._detect_severity(code)
            
            output += f"### {code}: {title}\n"
            output += f"- **Severity**: {severity.name}\n"
            output += f"- **Description**: {template}\n\n"
    
    return output
```

#### Task 4.2: Migration Utility
```python
# tools/migrate_diagnostic_codes.py
def migrate_diagnostic_references(file_path: str):
    """Update diagnostic code references in external files"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    for old_code, new_code in LEGACY_CODE_MAPPING.items():
        content = content.replace(old_code, new_code)
    
    with open(file_path, 'w') as f:
        f.write(content)
```

## Phase 5: Cleanup (Week 7)

### Deliverables

1. **Legacy System Removal**
   - Remove backward compatibility layers
   - Remove legacy diagnostic creation code
   - Update all references to use new system

2. **Final Testing**
   - End-to-end testing of all components
   - Performance validation
   - Documentation validation

3. **Migration Completion**
   - Final migration report
   - Updated README and documentation
   - Release notes for next version

### Implementation Tasks

#### Task 5.1: Legacy Code Cleanup
- Remove `LegacyDiagnosticAdapter`
- Remove `LEGACY_CODE_MAPPING`
- Update all direct `Diagnostic()` constructor calls to use `Diagnostic.create()`
- Remove old diagnostic creation patterns

#### Task 5.2: Final Validation
```python
# tests/integration/test_migration_complete.py
def test_no_legacy_diagnostic_creation():
    """Ensure no legacy diagnostic creation patterns remain"""
    
def test_all_components_use_xccss():
    """Verify all components use XCCSS format codes"""
    
def test_diagnostic_registry_complete():
    """Validate registry contains all expected diagnostics"""
```

## Risk Mitigation

### Technical Risks

1. **Breaking Changes**: Mitigated by backward compatibility layer
2. **Performance Degradation**: Mitigated by performance testing in each phase
3. **Missing Diagnostics**: Mitigated by comprehensive code review and testing

### Process Risks

1. **Timeline Delays**: Built-in buffer time and incremental delivery
2. **Team Coordination**: Clear phase boundaries and deliverables
3. **External Dependencies**: Early communication with external tool maintainers

## Success Criteria

### Phase Completion Criteria

1. **All tests pass** for the migrated components
2. **No performance regression** in diagnostic creation/processing
3. **Backward compatibility maintained** until Phase 5
4. **Documentation updated** to reflect changes

### Final Success Criteria

1. **100% migration** to XCCSS format
2. **Zero legacy code** remaining in codebase
3. **All external tools updated** or provided migration path
4. **Performance equal or better** than original system
5. **Enhanced capabilities** for language server integration

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | Week 1-2 | Foundation infrastructure |
| Phase 2 | Week 3 | Parser migration complete |
| Phase 3 | Week 4-5 | All components migrated |
| Phase 4 | Week 6 | Tools and documentation updated |
| Phase 5 | Week 7 | Cleanup and final validation |

**Total Duration**: 7 weeks
**Team Effort**: ~1.5 FTE weeks per phase
**Total Effort**: ~10 FTE weeks