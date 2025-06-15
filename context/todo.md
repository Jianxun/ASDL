# Project Todo List

## Current Sprint

### Setup & Planning
- [X] Setup context management files
- [X] Analyze ASDL schema v0.4 structure
- [X] Review architecture decisions with user
- [X] Update schema field name from `design_info` to `file_info`
- [X] Implement basic Python class definitions and data structures
- [X] Define interfaces between parser, resolver, and generator
- [ ] Create detailed implementation plan

### Core Implementation (Pending Architecture Decisions)
- [ ] Implement ASDL data structure classes
- [ ] Implement YAML parser for ASDL format
- [ ] Implement pattern expansion system (`<p,n>`, `[3:0]`)
- [ ] Implement parameter resolution system
- [ ] Implement SPICE netlist generator
- [ ] Create comprehensive test suite

### ASDLFile Round-trip & Debug Features (New Requirements)
- [ ] Add `save_to_file(filepath: str)` method to `ASDLFile` class
- [ ] Add `to_yaml()` method to convert `ASDLFile` back to YAML string
- [ ] Add `to_json()` method to `ASDLFile` class for debugging
- [ ] Add `dump_json(filepath: str)` method to save JSON representation
- [ ] Ensure round-trip preservation of YAML structure and data integrity (original `ASDLFile` only)
- [ ] Write tests for round-trip functionality (YAML → ASDLFile → YAML) - original data only
- [ ] Write tests for JSON serialization and debugging output
- [ ] Document round-trip limitation: only guaranteed before pattern expansion/parameter resolution

### Development Environment
- [ ] Verify virtual environment setup
- [ ] Install/verify all dependencies
- [ ] Setup development tools (black, flake8, pytest)
- [ ] Create initial source code structure

## Backlog

### Enhanced Features
- [ ] Support for multiple SPICE dialects (ngspice, spectre, etc.)
- [ ] Validation and error checking for ASDL inputs
- [ ] Layout intent handling and export
- [ ] Parameter optimization hints
- [ ] Hierarchical netlist support
- [ ] Integration with circuit simulators
- [ ] GUI or CLI interface for conversion

### Documentation & Examples
- [ ] Create comprehensive API documentation
- [ ] Add more example ASDL circuits
- [ ] Create tutorial/getting started guide
- [ ] Document design patterns and best practices

### Testing & Quality
- [ ] Unit tests for all core components
- [ ] Integration tests with real circuits
- [ ] Performance benchmarking
- [ ] Code coverage analysis
- [ ] Static type checking setup

## Completed Tasks
- [X] Initial project structure review
- [X] Context directory and files setup
- [X] Project requirements analysis
- [X] Schema field name update: `design_info` → `file_info`
- [X] Basic data structure implementation with placeholders
- [X] Processing pipeline class structure setup 