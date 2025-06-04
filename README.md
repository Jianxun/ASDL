# ASDL - Analog Structured Description Language

An intermediate representation for analog circuits that bridges the gap between human-friendly schematics and machine-friendly netlists.

## Overview

ASDL (Analog Structured Description Language) is a YAML-based format designed to capture not only the topological information of analog circuits but also their structural hierarchy and design intent. This makes it an ideal intermediate representation for:

- **Human designers**: More readable and editable than raw netlists
- **AI/ML systems**: Structured format suitable for training analog circuit design models  
- **EDA tools**: Standardized input/output format for circuit generation and optimization

## Key Features

- **Human-readable YAML syntax** with circuit hierarchy preservation
- **Design intent capture** through structured parameters and notes
- **Modular design** with reusable circuit building blocks
- **Pattern expansion** for symmetric circuit generation (`MN_{P,N}` → `MN_P`, `MN_N`)
- **Parameter substitution** system (`${M.diff}` style templating)
- **Multiple output formats** (SPICE, Spectre, Verilog-AMS)

## Project Structure

```
ASDL/
├── README.md              # This file
├── venv/                  # Virtual environment (not committed)
├── context/               # Project context tracking
│   ├── memory.md          # Project state and decisions
│   └── todo.md            # Task tracking
├── src/asdl/              # Main source code
│   ├── __init__.py
│   ├── parser.py          # YAML parsing and validation
│   ├── resolver.py        # Parameter and pattern resolution
│   ├── generator.py       # Netlist generation
│   └── utils.py           # Utility functions
├── tests/                 # Test suite
├── doc/                   # Documentation
│   ├── asdl_syntax.md     # ASDL syntax guide
│   └── ASDL_schema.md     # Complete schema documentation
├── examples/              # Example ASDL circuits
│   ├── ota_two_stg.yaml   # Two-stage Miller OTA
│   ├── ota.yaml           # Single-ended OTA variants
│   └── 311.asdl.yaml     # Other analog circuits
└── requirements.txt       # Python dependencies
```

## Quick Start

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ASDL
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

```python
from asdl import ASDLParser, SPICEGenerator

# Parse ASDL file
parser = ASDLParser()
circuit = parser.parse_file('examples/ota_two_stg.yaml')

# Generate SPICE netlist
generator = SPICEGenerator()
netlist = generator.generate(circuit)

# Write to file
with open('ota_two_stg.sp', 'w') as f:
    f.write(netlist)
```

## ASDL Syntax Overview

ASDL uses YAML with specific conventions for analog circuit description:

### Basic Module Structure
```yaml
modules:
  diff_pair_nmos:
    nets: {in_{p,n}: in, out_{p,n}: out, tail: io}
    parameters: {M: 2}
    circuits:
      - {<<: *NMOS, name: MN_{P,N}, S: tail, D: out_{p,n}, G: in_{p,n}, M: ${M}}
```

### Key Features
- **Pattern expansion**: `{p,n}` creates multiple variants
- **Parameter substitution**: `${M}` references parameters
- **YAML anchors**: `<<: *NMOS` for device templates
- **Hierarchical nets**: Support for `internal`, `in`, `out`, `io` roles

## Example Circuits

The repository includes several example circuits:

- **`ota_two_stg.yaml`**: Complete two-stage Miller OTA with bias generation
- **`ota.yaml`**: Various single-ended OTA configurations  
- **`311.asdl.yaml`**: Additional analog building blocks

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
The project follows PEP 8 guidelines with Black formatting:
```bash
black src/ tests/
flake8 src/ tests/
```

### Adding New Features
1. Write tests first (test-driven development)
2. Implement functionality
3. Update documentation
4. Update context files (`context/memory.md`, `context/todo.md`)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow test-driven development practices
4. Update documentation and context files
5. Submit a pull request

## Goals and Vision

ASDL aims to become a standard intermediate representation for analog circuit design, enabling:

- **AI-driven circuit design**: Training datasets for machine learning models
- **Design automation**: Automated circuit generation and optimization
- **Cross-tool compatibility**: Standardized format across EDA tools
- **Design knowledge preservation**: Capturing and sharing design intent

## License

[Specify license here]

## Contact

[Contact information] 