# XCCSS Diagnostic System Design Decisions

This document outlines the design decisions for the new XCCSS diagnostic code system, which replaces the previous `PXXX` numbering scheme with a more systematic and scalable approach.

## Background

The original diagnostic system used a simple component prefix plus sequential numbering (e.g., `P100`, `P101`, `P200`). While functional, this approach had several limitations:

1. **Inconsistent categorization**: No clear grouping of related errors
2. **Gap-prone numbering**: Manual assignment led to gaps and inconsistencies  
3. **Limited scalability**: Difficult to predict available number ranges
4. **Poor discoverability**: Error codes didn't indicate their nature

## Design Goals

The new XCCSS system addresses these issues with the following goals:

1. **Systematic Structure**: Predictable code format that encodes meaning
2. **Component Autonomy**: Each component manages its own diagnostics
3. **Central Validation**: Prevent conflicts without development friction
4. **Language Server Ready**: Support rich IDE features and tooling
5. **Scalable**: Support growth across all ASDL toolchain components
6. **Self-Documenting**: Codes that immediately convey error category

## XCCSS Format Specification

### Code Structure: `XCCSS`

- **X**: Component prefix (1 letter)
- **CC**: Category code (2 digits, 01-99)  
- **SS**: Specific error code within category (2 digits, 01-99)

### Component Prefixes

| Prefix | Component | Responsibility |
|--------|-----------|----------------|
| **P** | Parser | YAML parsing, document structure validation |
| **E** | Elaborator | Pattern expansion, parameter resolution |
| **V** | Validator | Semantic validation, cross-reference checking |
| **G** | Generator | Code generation, output formatting |
| **I** | Importer | Import resolution, dependency management |
| **S** | Schema | Schema validation, type checking |

### Category Classification

| Category | Code | Description | Typical Severity |
|----------|------|-------------|------------------|
| **Syntax** | `01` | YAML syntax, basic structure issues | Error |
| **Schema** | `02` | Required sections, mandatory fields | Error |
| **Semantic** | `03` | Business logic violations, consistency | Error |
| **Reference** | `04` | Missing references, circular dependencies | Error |
| **Type** | `05` | Type mismatches, conversion failures | Error |
| **Style** | `06` | Best practices, code quality | Warning |
| **Extension** | `07` | Unknown fields, forward compatibility | Warning |
| **Performance** | `08` | Performance hints, optimization suggestions | Info |

## Architecture Decisions

### Decision 1: Distributed Implementation with Central Validation

**Problem**: Should diagnostic definitions be centralized or distributed across components?

**Decision**: Hybrid approach - distributed implementation with central validation

**Rationale**:
- **Component Autonomy**: Each component defines its own diagnostics without external dependencies
- **Development Speed**: No registration overhead during development
- **Conflict Prevention**: Central registry validates uniqueness without blocking development
- **Maintainability**: Components can evolve diagnostic messages independently

**Implementation**:
```python
# Component-specific definitions
# src/asdl/parser/diagnostics.py
PARSER_DIAGNOSTICS = {
    "P0201": ("Missing Required Section", "'{section}' is mandatory"),
    "P0303": ("Module Type Conflict", "Module '{module}' has both templates")
}

# Central validation (development/test time only)
# src/asdl/diagnostics/registry.py
class DiagnosticRegistry:
    @classmethod
    def validate_no_conflicts(cls) -> List[str]:
        # Collect all diagnostic codes and check for duplicates
```

### Decision 2: Severity Encoding in Categories

**Problem**: How should diagnostic severity be determined?

**Decision**: Encode severity ranges in category numbers

**Rationale**:
- **Predictable**: Developers immediately know severity from code
- **Consistent**: Same category always maps to same severity
- **Tooling-Friendly**: LSP servers can determine severity without lookups
- **Self-Documenting**: Code format conveys both category and severity

**Encoding**:
- Categories 01-05: `ERROR` (compilation-blocking issues)
- Categories 06-07: `WARNING` (potential issues, compilation continues)  
- Category 08: `INFO` (hints and suggestions)

### Decision 3: Template-Based Message Generation

**Problem**: How to handle parameterized diagnostic messages?

**Decision**: Use Python string templates with named parameters

**Rationale**:
- **Type Safety**: Named parameters prevent positional errors
- **Flexibility**: Templates support rich message formatting
- **Consistency**: Standardized approach across all components
- **I18n Ready**: Template separation enables future internationalization

**Implementation**:
```python
# Template definition
"P0201": ("Missing Required Section", "'{section}' is mandatory at top level")

# Usage with parameters
Diagnostic.create("P0201", location=loc, section="file_info")
```

### Decision 4: Backward Compatibility Strategy

**Problem**: How to migrate from existing `PXXX` codes without breaking tools?

**Decision**: Phased migration with temporary compatibility layer

**Rationale**:
- **Gradual Transition**: Allows incremental migration of components
- **Tool Compatibility**: Existing tools continue working during transition
- **Risk Mitigation**: Problems can be caught and addressed incrementally
- **Documentation Alignment**: Maintains consistency during migration

**Migration Phases**:
1. **Infrastructure**: Create new diagnostic system alongside existing
2. **Component Migration**: Migrate components one by one with compatibility
3. **Tool Updates**: Update external tools to handle new codes
4. **Cleanup**: Remove old system after full migration

## Code Mapping Examples

### Parser Code Migration

| Old Code | New Code | Category | Description |
|----------|----------|----------|-------------|
| P100 | P0101 | Syntax | Invalid YAML Syntax |
| P101 | P0102 | Syntax | Invalid Root Type |
| P102 | P0201 | Schema | Missing Required Section |
| P103 | P0202 | Schema | Invalid Section Type |
| P104 | P0203 | Schema | Missing Required Field |
| P107 | P0303 | Semantic | Module Type Conflict |
| P108 | P0304 | Semantic | Incomplete Module Definition |
| P200 | P0701 | Extension | Unknown Top-Level Section |
| P301 | P0601 | Style | Dual Parameter Syntax |

### Elaborator Code Examples

| New Code | Category | Description |
|----------|----------|-------------|
| E0101 | Syntax | Empty Pattern |
| E0102 | Syntax | Single-Item Pattern |  
| E0301 | Semantic | Pattern Count Mismatch |
| E0401 | Reference | Undefined Parameter |

## Benefits and Trade-offs

### Benefits

1. **Systematic Organization**: Errors grouped by logical category
2. **Predictable Scaling**: Clear numbering allows up to 9,801 codes per component
3. **Self-Documenting**: Code structure immediately conveys error nature
4. **Tool Integration**: Structured format supports rich IDE features
5. **Component Independence**: Each component manages its diagnostics autonomously
6. **Conflict Prevention**: Central validation without development overhead

### Trade-offs

1. **Migration Cost**: Requires updating existing tools and documentation
2. **Code Length**: 5 characters vs 4 in old system (minimal impact)
3. **Learning Curve**: Developers need to understand new category system
4. **Complexity**: More sophisticated than simple sequential numbering

## Future Extensibility

The XCCSS system is designed for future growth:

1. **New Components**: Easy to add new component prefixes (D, T, L, etc.)
2. **Category Evolution**: New categories can be added within the 01-99 range
3. **Language Server Features**: Rich diagnostic metadata supports IDE integration
4. **Cross-Component Analysis**: Systematic codes enable better tooling correlation
5. **Documentation Generation**: Structured format supports automated doc generation

### Decision 5: Automated Documentation Generation

**Problem**: How to maintain consistent and up-to-date diagnostic documentation across all components?

**Decision**: Implement automated documentation generation that aggregates all error codes from distributed component definitions

**Rationale**:
- **Single Source of Truth**: Component diagnostic definitions drive documentation
- **Consistency**: Automated generation eliminates manual sync issues
- **Completeness**: Ensures all defined diagnostics are documented
- **CI/CD Integration**: Documentation updates automatically with code changes
- **Multi-Format Support**: Generate different formats for different audiences

**Implementation Approach**:
```python
# tools/generate_diagnostic_docs.py
class DiagnosticDocumentationGenerator:
    """Automated documentation generator for XCCSS diagnostic system"""
    
    def generate_complete_reference(self) -> str:
        """Generate comprehensive diagnostic code reference"""
        # Scan all component diagnostic definitions
        # Generate organized documentation by component and category
        # Include examples, severity levels, and suggestions
    
    def generate_migration_guide(self) -> str:
        """Generate migration guide from legacy to XCCSS codes"""
        # Cross-reference old and new codes
        # Generate mapping tables and conversion utilities
    
    def generate_lsp_metadata(self) -> Dict:
        """Generate Language Server Protocol metadata"""
        # Export diagnostic info for IDE integration
        # Include quick fix suggestions and code actions
```

**Documentation Outputs**:
- **Complete Reference**: Comprehensive diagnostic code documentation
- **Migration Guide**: Legacy to XCCSS code mapping and conversion tools
- **LSP Metadata**: Structured data for language server integration
- **CLI Help**: Command-line tool integrated help and error explanations

## Conclusion

The XCCSS diagnostic system provides a robust, scalable foundation for the ASDL toolchain's diagnostic needs. While requiring migration effort, it positions the system for future growth including language server development and enhanced tooling integration.

The distributed implementation with central validation strikes the right balance between component autonomy and system coherence, supporting both current needs and future extensibility.