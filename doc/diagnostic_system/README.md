# ASDL Diagnostic System Documentation

This directory contains comprehensive documentation for the ASDL diagnostic system, including the new XCCSS format specification and migration from the legacy system.

## Document Overview

### Core Documentation

- **[diagnostic_codes.md](diagnostic_codes.md)** - Current diagnostic codes reference (legacy format)
- **[linter_compiler_architecture.md](linter_compiler_architecture.md)** - Tooling architecture for linter/compiler integration

### XCCSS System Documentation

- **[xccss_design_decisions.md](xccss_design_decisions.md)** - Design rationale and trade-offs for the new XCCSS format
- **[xccss_architecture.md](xccss_architecture.md)** - Technical architecture and component interactions
- **[xccss_migration_plan.md](xccss_migration_plan.md)** - Detailed implementation plan for migrating to XCCSS

## Quick Reference

### Current System (Legacy)
- **Format**: `PXXX` (e.g., P100, P201)
- **Errors**: 100-199 range
- **Warnings**: 200-299 range
- **Components**: P (Parser), E (Elaborator), V (Validator), G (Generator)

### New XCCSS System  
- **Format**: `XCCSS` (e.g., P0101, E0301, V0401)
- **Components**: X = P, E, V, G, I, S
- **Categories**: CC = 01-08 (Syntax, Schema, Semantic, Reference, Type, Style, Extension, Performance)
- **Specific Codes**: SS = 01-99 within each category

## Migration Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | 🔄 Planned | Foundation infrastructure setup |
| Phase 2 | ⏳ Pending | Parser migration to XCCSS format |
| Phase 3 | ⏳ Pending | Elaborator, Validator, Generator migration |
| Phase 4 | ⏳ Pending | Tool updates and documentation |
| Phase 5 | ⏳ Pending | Cleanup and legacy system removal |

## Key Benefits of XCCSS

1. **Systematic Organization**: Errors grouped by logical category
2. **Predictable Scaling**: Up to 9,801 codes per component (99 categories × 99 codes)
3. **Self-Documenting**: Code structure immediately conveys error nature
4. **Language Server Ready**: Structured format supports rich IDE features
5. **Component Autonomy**: Each component manages its diagnostics independently

## For Developers

### Adding New Diagnostics (Current System)
1. Choose appropriate component prefix (P, E, V, G)
2. Select number in appropriate range (100-199 for errors, 200-299 for warnings)
3. Add entry to [diagnostic_codes.md](diagnostic_codes.md)
4. Update component's diagnostic creation code

### Adding New Diagnostics (XCCSS System - Future)
1. Choose component prefix (P, E, V, G, I, S)
2. Select appropriate category (01-08)
3. Choose next available specific code (01-99)
4. Add to component's diagnostic dictionary
5. Registry validation ensures no conflicts

### Category Reference (XCCSS)

| Category | Code | Description | Severity |
|----------|------|-------------|----------|
| Syntax | 01 | YAML syntax, basic structure | Error |
| Schema | 02 | Required sections, mandatory fields | Error |
| Semantic | 03 | Business logic violations | Error |
| Reference | 04 | Missing references, circular deps | Error |
| Type | 05 | Type mismatches, conversions | Error |
| Style | 06 | Best practices, code quality | Warning |
| Extension | 07 | Unknown fields, forward compatibility | Warning |
| Performance | 08 | Performance hints, optimization | Info |

## For Tool Developers

### Current Integration
- Parse diagnostic codes from compiler/linter output
- Handle P100-199 as errors, P200-299 as warnings
- Reference [diagnostic_codes.md](diagnostic_codes.md) for descriptions

### Future Integration (XCCSS)
- Parse XCCSS format codes (5 characters: XCCSS)
- Auto-detect severity from category code (CC)
- Leverage structured diagnostic registry for rich features
- Support language server protocol integration

## Related Documentation

- **Language Server Development**: See XCCSS architecture for LSP integration patterns
- **Testing Strategy**: See migration plan for validation and testing approaches
- **Performance Considerations**: See architecture document for optimization details

## Contributing

When updating diagnostic documentation:

1. **Maintain Consistency**: Follow established patterns and formatting
2. **Include Examples**: Provide both incorrect and correct code examples
3. **Update All References**: Ensure cross-document consistency
4. **Test Documentation**: Validate examples actually trigger described diagnostics

## Questions and Support

For questions about the diagnostic system:

1. **Design Questions**: Refer to [xccss_design_decisions.md](xccss_design_decisions.md)
2. **Implementation Questions**: Refer to [xccss_architecture.md](xccss_architecture.md)
3. **Migration Questions**: Refer to [xccss_migration_plan.md](xccss_migration_plan.md)
4. **Current System**: Refer to [diagnostic_codes.md](diagnostic_codes.md)