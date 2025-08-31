# ASDL Tooling Architecture: Linter and Compiler

This document outlines the architectural decisions for refactoring the ASDL tooling to support both a standalone linter and the existing ASDL-to-SPICE compiler, with a focus on maximizing code reuse.

## The Challenge

The goal is to create a new ASDL linter that can check for semantic and structural errors in ASDL YAML files. Much of the validation logic required for a linter (e.g., checking for undeclared nets, unused components) is already present or needed within the compiler pipeline. The challenge is to architect the project so that this logic is written once and shared between both tools.

## Initial Proposal: A Single Validation Stage

The initial idea was a classic three-stage compiler architecture:

1.  **Front-End (Shared):** `parser.py` and `elaborator.py` would parse and elaborate the ASDL source into an `ASDLFile` object (our Intermediate Representation or IR).
2.  **Middle-End (Shared):** A new `validator.py` module would run all semantic checks on the expanded `ASDLFile`.
3.  **Back-End (Specific):** The `linter` would report the validator's findings, while the `compiler` (`generator.py`) would use the validated `ASDLFile` to produce SPICE.

This led to the following architectural diagram:

```mermaid
graph TD;
    subgraph "Front-End (Shared)"
        direction LR
        A["ASDL YAML"] --> B["Parser & Elaborator"];
        B --> C["ASDLFile (IR)"];
    end

    subgraph "Middle-End (Shared)"
        direction LR
        C --> D["validator.py<br/>(Runs All Checks)"];
        D --> E["Validation Results<br/>(Errors/Warnings)"];
    end

    subgraph "Back-Ends (Separate Tools)"
        direction TB
        E --> F["Linter<br/>(Formats & Prints Results)"];
        
        subgraph "Compiler Pipeline"
            direction TB
            D -- "If no fatal errors" --> G["generator.py<br/>(SPICE Generation)"];
            G --> H["SPICE Netlist"];
        end
    end

    style F fill:#ddeeff,stroke:#333;
    style G fill:#ddffdd,stroke:#333;
    style H fill:#ddffdd,stroke:#333;
```

## The Refinement: Handling Errors During Elaboration

A key insight was raised: **What about errors that occur during the elaboration phase itself?** For example, if a pattern has mismatched item counts (`G_<p,n>: in_p`) or unresolved parameters. Under the initial proposal, the elaborator would likely crash with an exception, which is poor behavior for a linter that should report as many errors as possible in one go.

This led to a more sophisticated and robust architecture.

## Final Architecture: Multi-Stage Validation Pipeline

The final design treats validation as a continuous process that occurs throughout the analysis pipeline. Both the elaborator and a dedicated validator will generate diagnostic messages. This design fully supports the unified module architecture where both primitive and hierarchical modules are processed through the same pipeline.

1.  **Front-End (Parsing):** The `parser` produces a raw `ASDLFile` object from the source YAML.

2.  **Middle-End (Analysis Pipeline):**
    *   **Stage 1: The Elaborator (`elaborator.py`)**: This stage now acts as the first analysis step. It performs pattern expansion, parameter/variable resolution, and handles both primitive and hierarchical modules in the unified architecture. Instead of raising exceptions on errors, it **logs them as diagnostic messages** and continues processing where possible. It outputs both the (potentially partially) elaborated `ASDLFile` and a list of diagnostics.
    *   **Stage 2: The Validator (`validator.py`)**: This stage takes the elaborated `ASDLFile` and the list of diagnostics from the previous stage. It runs its own semantic checks (e.g., unused components, net validation) on the successfully elaborated parts of the design and **appends its findings** to the diagnostic list.

3.  **Back-End (Tool-Specific Consumers):**
    *   **Linter:** Runs the full analysis pipeline and then simply formats and prints the complete, combined list of diagnostics.
    *   **Compiler:** Runs the same analysis pipeline. It then inspects the list of diagnostics. If any fatal errors are present, it aborts. Otherwise, it proceeds to the `SPICEGenerator` to create the netlist. The unified module architecture ensures consistent processing for both primitive and hierarchical modules throughout this pipeline.

This refined architecture is visualized below:

```mermaid
graph TD;
    A["ASDL YAML"] --> B["Parser"];
    B --> C["ASDLFile (raw)"];

    subgraph "Analysis Pipeline (Middle-End)"
        direction TB
        C --> D["Elaborator"];
        D --> E{"Elaborated ASDLFile<br/>(partially if errors)"};
        D -- "Produces" --> F["Elaboration Diagnostics<br/>(e.g., mismatched patterns, unresolved parameters)"];
        
        E --> G["Validator"];
        G -- "Takes" --> F;
        G -- "Appends" --> H["Semantic Diagnostics<br/>(e.g., unused components)"];
    end

    subgraph "Tool Back-Ends"
        direction TB
        H --> I["Linter<br/>(Formats & Prints all diagnostics)"];
        
        subgraph "Compiler"
            direction TB
            H --> J{"Check for Fatal Errors"};
            J -- "No Errors" --> K["Generator"];
            K --> L["SPICE Netlist"];
            J -- "Errors Found" --> M["Abort"];
        end
    end

    style I fill:#ddeeff,stroke:#333;
    style Compiler fill:#ddffdd,stroke:#333;
```

This final design is more robust, provides a better user experience for the linter, and maintains a clean separation of concerns. 