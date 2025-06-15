# Project Todo List

## Current Sprint - SPICE Generator Implementation

### Core Implementation (In Progress)
- [X] Implement ASDL data structure classes (with future-proofing)
- [X] Implement YAML parser for ASDL format (with extensibility features) - **44 PASSING TESTS**
- [ ] **Implement SPICE netlist generator (CURRENT PRIORITY - TDD in progress)**
  - [X] **Phase 1: Device Generation** (`tests/unit_tests/generator/test_device_generation.py`) ✅ **COMPLETE - 7 PASSING TESTS**
    - [X] `test_generate_simple_resistor()` - Basic device line generation
    - [X] `test_generate_capacitor()` - Different device type handling
    - [X] `test_generate_inductor()` - Another device type
    - [X] `test_generate_device_with_parameters()` - Device with parameter values (NMOS with correct SPICE node order)
    - [X] `test_generate_device_invalid_model()` - Error handling for missing model
    - [X] `test_device_template_extensibility()` - Template system flexibility (diode example)
    - [X] `test_spice_node_ordering_verification()` - **SPICE node order verification for all device types**
  - [ ] **Phase 2: Net and Port Handling** (`tests/unit_tests/generator/test_nets_and_ports.py`)
    - [ ] `test_simple_net_connection()` - Basic net connectivity
    - [ ] `test_port_to_net_mapping()` - Port-to-net resolution
    - [ ] `test_multiple_nets()` - Multiple net handling
    - [ ] `test_unconnected_port_error()` - Error for unconnected ports
    - [ ] `test_net_name_sanitization()` - SPICE-compatible net names
  - [ ] **Phase 3: Module/Subcircuit Generation** (`tests/unit_tests/generator/test_module_generation.py`)
    - [ ] `test_empty_module_subckt()` - Basic .subckt wrapper
    - [ ] `test_module_with_single_device()` - Module containing one device
    - [ ] `test_module_port_ordering()` - Port order in .subckt definition
    - [ ] `test_module_with_multiple_devices()` - More complex modules
    - [ ] `test_nested_module_hierarchy()` - Module instantiation within modules
  - [ ] **Phase 4: Complete SPICE Output** (`tests/unit_tests/generator/test_spice_output.py`)
    - [ ] `test_header_generation()` - SPICE file header/title
    - [ ] `test_model_statements()` - .model card generation
    - [ ] `test_complete_simple_circuit()` - End-to-end simple circuit
    - [ ] `test_spice_file_structure()` - Proper SPICE file organization
    - [ ] `test_end_statement()` - Proper .end termination
  - [ ] **Phase 5: Parameter Handling** (`tests/unit_tests/generator/test_parameters.py`)
    - [ ] `test_resolved_parameter_values()` - Pre-resolved parameter handling
    - [ ] `test_unresolved_parameter_error()` - Error for unresolved parameters
    - [ ] `test_parameter_in_device_value()` - Parameters in device values
    - [ ] `test_parameter_in_module_instance()` - Module instance parameters
  - [ ] **Phase 6: Error Handling** (`tests/unit_tests/generator/test_error_handling.py`)
    - [ ] `test_missing_model_reference()` - Handle missing model definitions
    - [ ] `test_invalid_device_type()` - Unknown device types
    - [ ] `test_circular_module_reference()` - Detect circular dependencies
    - [ ] `test_duplicate_module_names()` - Handle name conflicts
    - [ ] `test_invalid_port_connections()` - Port connection validation
  - [ ] **Phase 7: Metadata and Comments** (`tests/unit_tests/generator/test_metadata.py`)
    - [ ] `test_module_documentation_comments()` - Doc strings as comments
    - [ ] `test_file_info_header_comment()` - File info in header
    - [ ] `test_device_intent_comments()` - Intent metadata as comments
    - [ ] `test_comment_formatting()` - Proper SPICE comment syntax
  - [ ] **Phase 8: Integration Testing** (`tests/unit_tests/generator/test_integration.py`)
    - [ ] `test_end_to_end_simple_amplifier()` - Complete circuit example
    - [ ] `test_parser_to_generator_pipeline()` - Full YAML → SPICE flow
    - [ ] `test_differential_pair_basic()` - Simple diff pair (no patterns)
    - [ ] `test_multi_level_hierarchy()` - Complex module nesting

### Future Sprints
- [ ] Implement parameter resolution system
- [ ] Implement pattern expansion system (`<p,n>`, `[3:0]`)
- [ ] Create comprehensive test suite for end-to-end pipeline

### ASDLFile Round-trip & Debug Features (Next Sprint)
- [ ] Add `save_to_file(filepath: str)` method to `ASDLFile` class
- [ ] Add `to_yaml()` method to convert `ASDLFile` back to YAML string
- [ ] Add `to_json()` method to `ASDLFile` class for debugging
- [ ] Add `dump_json(filepath: str)` method to save JSON representation
- [ ] Ensure round-trip preservation of YAML structure and data integrity (original `ASDLFile` only)
- [ ] Write tests for round-trip functionality (YAML → ASDLFile → YAML) - original data only
- [ ] Write tests for JSON serialization and debugging output
- [ ] Document round-trip limitation: only guaranteed before pattern expansion/parameter resolution

## Setup & Planning ✅ COMPLETED
- [X] Setup context management files
- [X] Analyze ASDL schema v0.4 structure
- [X] Review architecture decisions with user
- [X] Update schema field name from `design_info` to `file_info`
- [X] Implement basic Python class definitions and data structures
- [X] Define interfaces between parser, resolver, and generator
- [X] Create detailed implementation plan
- [X] Update implementation plan with current sprint status

## Development Environment ✅ COMPLETED
- [X] Verify virtual environment setup
- [X] Install/verify all dependencies
- [X] Setup development tools (black, flake8, pytest)
- [X] Create initial source code structure

## Backlog

### Enhanced Features
- [ ] Support for multiple SPICE dialects (ngspice, spectre, etc.)
- [ ] Validation and error checking for ASDL inputs
- [ ] Layout intent handling and export
- [ ] Parameter optimization hints
- [ ] Hierarchical netlist support
- [ ] Integration with circuit simulators
- [ ] GUI or CLI interface for conversion
- [ ] Port constraints implementation and processing
- [ ] Advanced constraint validation and checking

### Documentation & Examples
- [ ] Create comprehensive API documentation
- [ ] Add more example ASDL circuits
- [ ] Create tutorial/getting started guide
- [ ] Document design patterns and best practices

### Testing & Quality
- [ ] Unit tests for all core components ✅ PARSER COMPLETE (44 tests)
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
- [X] **Complete ASDL parser implementation with comprehensive test suite (44 passing tests)**
- [X] **Future-proofing parser with extensibility features and validation modes**
- [X] **Error handling and backward compatibility for schema versions**
- [X] **Unknown field detection and intent metadata preservation**
- [X] Updated implementation plan to reflect current sprint focus 