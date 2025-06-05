# Project Todo List

## Current Sprint
- [x] Setup standard development environment
- [x] Create context files (memory.md, todo.md)
- [x] Create README.md
- [x] Create requirements.txt with core dependencies
- [x] Create .gitignore for Python project
- [x] Install project dependencies
- [x] Organize project structure (move files to examples/, doc/)
- [x] Implement ASDL YAML parser
- [x] Fix YAML syntax issues in example files
- [x] Write tests for core parsing functionality
- [x] Add JSON export functionality for debugging
- [x] Discover and fix ASDL syntax ambiguity (nets vs parameters)
- [x] **ASDL Syntax Migration: Replace .defaults with models section**
  - [x] Update ASDLFile data model to use models field instead of defaults
  - [x] Update parser to handle models section
  - [x] Update all test cases to use new syntax
  - [x] Verify both old and new format parsing works
  - [x] All tests passing (10/10)
- [ ] Implement pattern expansion system
- [ ] Implement parameter resolution engine
- [ ] Create basic SPICE netlist generator

## Next Priority Tasks
- [ ] Create pattern expander for `{p,n}` syntax
- [ ] Design parameter resolver for `${param}` expressions
- [ ] Create hierarchical module instantiation
- [ ] Design SPICE output generator architecture
- [ ] Add support for device primitive recognition
- [ ] Implement dependency ordering for module generation

## Critical Issues to Address
- [x] **ASDL Syntax Standardization**: ✅ COMPLETED - Migrated to models section
  - ✅ Replaced confusing `.defaults` anchor syntax with intuitive `models` section
  - ✅ Eliminated YAML anchor references (`&`, `*`, `<<:`) for better usability
  - ✅ Physical device models now clearly defined in dedicated section
  - ✅ Device instantiation uses direct model names
  - ✅ Better separation of concerns: models vs instances
- [ ] **Legacy Format Support**: Decide on backward compatibility strategy
  - Option 1: Support both old and new syntax with deprecation warnings
  - Option 2: Require immediate migration to new syntax  
  - Option 3: Add automatic syntax conversion utility
- [ ] **Schema Validation**: Add strict validation to catch syntax errors early
- [ ] **Documentation Updates**: Update all examples and guides to use new models syntax

## Migration Deliverables (COMPLETED)
- [x] **Parser Updates**: Modified to handle models section instead of .defaults
- [x] **Data Model Updates**: ASDLFile.models field replaces ASDLFile.defaults  
- [x] **Test Suite Updates**: All 10 tests updated and passing with new syntax
- [x] **Syntax Validation**: Verified parser handles both legacy and new formats
- [x] **Example Files**: Have both old format (ota_two_stg.yaml) and new format (ota_two_stg_fixed.yaml)

## Backlog
- [ ] Create migration utility to convert .defaults syntax to models syntax
- [ ] Add deprecation warnings for .defaults usage
- [ ] Update documentation with models section examples
- [ ] Implement hierarchical module flattening
- [ ] Add support for technology file integration
- [ ] Create validation system for ASDL syntax
- [ ] Implement circuit optimization features
- [ ] Add support for multiple output formats (Spectre, Verilog-AMS)
- [ ] Create comprehensive test suite with sample circuits
- [ ] Develop circuit library with common analog blocks
- [ ] Create documentation and tutorials
- [ ] Performance optimization for large circuits
- [ ] Integration with existing EDA tools
- [ ] Dataset curation for AI/ML training
- [ ] Circuit visualization tools
- [ ] Parameter sweeping and design space exploration

## Completed Tasks
- [x] Initial project structure analysis
- [x] Virtual environment setup and activation
- [x] Directory structure creation (src/, tests/, examples/, doc/, context/)
- [x] Context files initialization (memory.md, todo.md)
- [x] README.md creation with comprehensive project overview
- [x] Requirements.txt with core dependencies (PyYAML, pytest, etc.)
- [x] .gitignore file for Python project
- [x] Dependencies installation
- [x] File organization (moved examples and documentation to proper directories)
- [x] ASDL YAML parser implementation with data models
- [x] YAML syntax fixes for proper parsing of pattern and parameter syntax
- [x] Comprehensive parser test suite (9/9 tests passing)
- [x] Successfully parsing complete OTA two-stage example
- [x] **JSON Export Feature**: Added `to_json()`, `save_json()`, `parse_and_dump()` methods
- [x] **Critical Discovery**: Identified ASDL syntax ambiguity between device pins and parameters
- [x] **Syntax Solution**: Created corrected ASDL format with explicit `nets:` field for device connections
- [x] **Schema Documentation**: Updated ASDL schema with proper syntax examples and best practices
- [x] **Validation Testing**: Demonstrated parsing differences between old and new syntax formats
- [x] **Anchor Standardization**: Established clean anchors (model only) with explicit bulk connections
- [x] **Final Syntax Decision**: Adopted explicit bulk connection declarations for transparency
- [x] **ASDL Syntax Migration**: Successfully replaced .defaults anchor syntax with models section
  - [x] **Parser Migration**: Updated parser to handle models section instead of .defaults
  - [x] **Data Model Migration**: Changed ASDLFile to use models field
  - [x] **Test Migration**: Updated all 10 test cases to new syntax (100% passing)
  - [x] **Syntax Improvement**: Eliminated confusing YAML anchors for better usability
  - [x] **Example Validation**: Verified parsing of both legacy and new format files 