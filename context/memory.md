# Project Memory

## Project Overview
ASDL (Analog Structured Description Language) is an intermediate representation for analog circuits that bridges the gap between human-friendly schematics and machine-friendly netlists. The goal is to create a YAML-based format that captures not only topological information but also structural and design intent information.

The objective is to develop a plain text intermediate representation that:
- Is more human-friendly than raw netlists but more machine-processable than schematics
- Carries topological information AND structural/design intent
- Can be used to curate datasets for training AI models for analog circuit design
- Serves as a bridge between design tools and AI systems

## Current State
- **Development environment**: Fully set up with Python virtual environment
- **Project structure**: Standard Python project layout implemented
- **Dependencies**: All required packages installed (PyYAML, pytest, black, flake8, etc.)
- **Documentation**: README.md created with comprehensive project overview
- **Context tracking**: memory.md and todo.md files established
- **Example circuits**: Available in examples/ directory (ota_two_stg.yaml, ota_concise.yaml)
- **Documentation**: Existing syntax guide and schema in doc/ directory

## Key Decisions
- Using YAML as the base format for ASDL due to its human readability and structured nature
- Supporting hierarchical circuit descriptions with modular building blocks
- Including parameter substitution (`${param}`) and pattern expansion (`MN_{P,N}`)
- Maintaining design intent through `notes` sections and structured parameters
- Supporting both flattened and hierarchical circuit representations
- Following Python best practices with virtual environment and test-driven development
- Using standard project structure: src/asdl/, tests/, examples/, doc/, context/

## Open Questions
- What SPICE simulators should be primarily targeted for netlist generation?
- Should the converter support multiple output formats (SPICE, Spectre, Verilog-AMS)?
- What level of optimization should be included in the conversion process?
- How should we handle technology-specific device models in the YAML format?
- What should be the primary AI/ML use cases for the dataset?

## Technical Architecture
- YAML anchors and aliases for device template reuse
- Parameter resolution system for `${param}` expressions
- Pattern expansion engine for `{p,n}` style instantiation
- Hierarchical module system with net role declarations (in/out/io/internal)
- Support for primitive devices (NMOS, PMOS, R, C, L) and custom modules

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