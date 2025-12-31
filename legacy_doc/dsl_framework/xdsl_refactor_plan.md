Analysis of ASDL Compiler Architecture and Refactor Plan for xDSL
Current Architecture
AST Data Structures
The parser produces a simple abstract syntax tree (AST) represented by Python dataclasses. The ASDLFile dataclass stores the top‐level file information (file_info), imported modules, model aliases and a dictionary of Module objects. Each Module contains fields such as doc, ports, internal_nets, parameters, variables, spice_template, instances, pdk and metadata. Mutual exclusion between spice_template and instances is enforced so a module is either primitive (Spice) or hierarchical
github.com
. Ports are represented by Port objects with a direction/type, while instances of modules are stored in a dictionary keyed by instance identifiers.
Parser
The parser (src/asdl/parser) loads YAML/JSON input, validates the top level and dispatches to section parsers. The top‐level function parse_file calls parse_string, which loads the YAML with a diagnostic wrapper, validates the file_info section and uses dedicated parsers (file_info_parser, import_parser, module_parser, etc.) to construct the AST
github.com
. Unknown fields or invalid sections are detected by the FieldValidator
github.com
 and the DualSyntaxResolver ensures canonical parameters/variables naming
github.com
. The parser thus produces a tree of dataclasses rather than a formal IR.
Elaborator
The elaborator performs several transformations:
Pattern expansion: Literal (<p,n>) and bus ([msb:lsb]) patterns in port names, nets and instance identifiers are expanded into explicit entries. The implementation includes detection of literal and bus patterns and error checking (empty pattern, single element, invalid bus range, mixed patterns)
github.com
.
Variable resolution: Instance parameters that match variable names defined in a module’s variables field are replaced with the variable value, while undefined variables produce diagnostics
github.com
.
Environment variable resolution: Parameter values and primitive module templates that match the pattern ${VAR} are replaced by environment variables. Invalid formats or missing environment variables emit diagnostics
github.com
github.com
.
Import resolution: A separate import system builds a dependency graph, loads imported .asdl files, validates qualified references/aliases and flattens modules. The PathResolver reads the ASDL_PATH environment variable and resolves files
github.com
. FileLoader caches parsed files and detects circular dependencies
github.com
. DependencyGraphBuilder builds a graph of import relationships, resolves alias mappings and emits diagnostics for missing or ambiguous files
github.com
. ReferenceValidator checks that qualified instance references and model aliases are valid, emitting diagnostics when modules or aliases are missing
github.com
. Flattener rewrites instance model names by stripping import alias prefixes and resolving model aliases; it merges imported modules into the main file, applying a merge policy (LOCAL_WINS vs IMPORT_WINS)
github.com
. The import system returns a flattened ASDLFile and diagnostics.
Elaboration orchestration: The Elaborator class calls the pattern expander, variable resolver and environment resolver sequentially to produce a new ASDLFile object and diagnostics
github.com
.
Validator
The validator defines rule interfaces (ModuleRule, FileRule) and a runner that executes rules on each module or on the file. Default rules include:
Port mapping rule: Validates that instance port mappings only refer to ports defined on the target module. Instances mapping ports on modules with no ports (V0301) or mapping unknown ports (V0302) produce diagnostics
github.com
.
Parameter overrides rule: Hierarchical modules cannot have parameters; overriding variables is forbidden and overriding non-existent parameters yields diagnostics (V0303–V0305)
github.com
.
Net declarations rule: Would warn when nets used in instance mappings are undeclared (V0401), but this check is currently suppressed
github.com
.
Module parameters rule: Declaring parameters on hierarchical modules is invalid (V0201)
github.com
.
Unused modules rule: Would warn about modules that are never instantiated (V0601), but it is also suppressed
github.com
.
The validator uses XCCSS‐style codes and severity mapping similar to the elaborator diagnostics
github.com
.
CLI and tooling
Command‑line tools wrap the parser, elaborator and validator. For example, validate performs parse → elaborate → validate and prints diagnostics
github.com
. The import system is exposed through an ImportCoordinator which orchestrates parsing, graph building, validation and flattening
github.com
.
Shortcomings of the Current Architecture
No explicit intermediate representation (IR): The compiler operates on Python dataclasses which represent AST nodes but lack IR semantics such as operations, blocks or dialects. Transformations (pattern expansion, variable resolution, import flattening) mutate or replace dataclasses without using a pass framework. This makes it difficult to introduce analyses, optimizations or code generation passes.
Lack of modular pass infrastructure: The elaborator manually calls pattern expansion, variable resolution and environment resolution in sequence; adding new transformations requires editing the elaborator. There is no generic pass manager or ability to run passes selectively.
Limited ability to attach metadata: Dataclasses carry basic location information but do not provide a standard way to annotate intermediate values or attach analyses results. Diagnostics rely on manually storing Locatable objects.
No separation between AST and IR: The AST dataclasses are used for both syntax representation and elaborated output. When additional semantics (pattern expansion, import flattening) are applied, the same structures are mutated or replaced, blurring the line between parsed syntax and elaborated representation.
Adopting xDSL – Overview
xDSL is a Python framework for constructing MLIR‑like intermediate representations. It provides classes such as IRModule, Block, Operation, Attribute and Type and allows users to define custom dialects with operations and attributes. xDSL also comes with a pass infrastructure for running transformations and analyses. Adopting xDSL would modernize the ASDL compiler by introducing:
A formal IR: Modules, instances and nets would become operations in a custom ASDL dialect. Each operation can carry attributes (e.g., parameter dictionaries) and results (e.g., nets). An IRModule would hold all module definitions as regions.
Passes: Pattern expansion, variable resolution, import flattening and validation rules can be implemented as passes over the IR. xDSL’s pass manager can orchestrate these passes.
Separation of concerns: The parser continues to produce an AST (dataclasses) that closely reflects the YAML/JSON syntax. A dedicated conversion layer translates AST to IR. All subsequent analyses and transformations operate on the IR, leaving the AST untouched.
Diagnostics support: xDSL operations include location attributes and support for attaching diagnostic information. This aligns with the existing use of Locatable for error reporting.
Proposed Refactor Plan
The refactor should proceed incrementally to reduce risk. The following plan outlines major steps:
1. Define an xDSL ASDL dialect
Design operations:
ModuleOp: Represents an ASDL module. Attributes include name, parameters, variables, ports and template (for primitive modules). It would have a single region containing a block. The block arguments correspond to port nets (similar to function arguments in MLIR). The block’s body contains InstanceOp and NetOp operations.
PortOp or attributes: Ports may be modeled as block arguments with direction attributes (input/output) or as dedicated operations nested under ModuleOp.
InstanceOp: Represents an instantiation of a module or primitive device. Attributes include instance_name, model_ref, parameters, mappings and location. It yields net results for each port on the instance, enabling further wiring.
NetOp (optional): Represents internal net declarations for hierarchical modules. Attributes include name and optionally an array length.
Additional operations could handle parameter or variable declarations explicitly.
Define attribute types: Create custom attribute classes for directions (in, out, inout), port types (e.g., analog, digital) and pattern expansions. Use xDSL’s Attribute base class.
Register the dialect: Provide an ASDL dialect class that registers all operations and attributes so xDSL can parse/print them.
2. AST to IR conversion
Write a converter that traverses the existing dataclass AST and constructs an xDSL IRModule. For each module in ASDLFile.modules, create a ModuleOp with a region:
Add block arguments for each port; store their names and directions in attributes.
Inside the block, emit NetOp operations for internal_nets.
Emit InstanceOp operations for each instance. For hierarchical instances, the model_ref attribute stores the module name; for primitive ones, store the spice_template string. Mappings between instance ports and nets become operands of InstanceOp or attributes.
Attach location information from the AST to each operation (xDSL supports optional location attribute for diagnostics).
Handle model aliases and imports during conversion: Use the existing import coordinator to produce a flattened ASDLFile. The conversion layer should run after flattening so that model_ref names refer directly to modules in the IR.
3. Implement elaboration passes using xDSL
The existing elaborator logic can be converted into passes:
Pattern expansion pass: Traverse each ModuleOp and for operations or attributes that contain literal <...> or bus [msb:lsb] patterns, expand them into multiple operations or update attributes accordingly. Since xDSL operations are easily mutable, a pass can replace operations or insert new ones.
Variable resolution pass: For each InstanceOp, examine its parameters attribute and replace parameter values that match variables defined in the parent ModuleOp with the variable value. Use xDSL’s symbol table to reference VariableOp definitions if variables become first‑class operations.
Environment variable pass: Similar to the current EnvVarResolver, traverse parameters and templates in operations and replace ${VAR} tokens using os.environ. Emit diagnostics via xDSL’s diagnostic engine when variables are missing or invalid.
Import flattening pass (optional): If import flattening is postponed to IR, create a pass that merges ModuleOp definitions from different files into a single IRModule and rewrites qualified model_ref attributes.
xDSL’s pass manager can orchestrate these passes, allowing them to be run selectively.
4. Implement validation as analysis passes
Each validator rule can be translated into an xDSL analysis pass that traverses the IR and emits diagnostics:
Port mapping check: For each InstanceOp, look up the target ModuleOp and verify that mapped ports match defined ports. Use xDSL’s symbol lookup to resolve the target module.
Parameter override check: Check that parameters are only overridden on primitive modules; for hierarchical modules, emit diagnostics. Verify that only declared parameters are overridden and that variables are not overridden.
Module parameters check: Ensure that hierarchical modules (ModuleOp with any InstanceOp operations) do not define parameters.
Additional suppressed rules (undeclared nets, unused modules) can be easily activated as passes.
Because xDSL provides a uniform IR and a pass infrastructure, validation passes can operate consistently over the IR. Diagnostics can include operation locations and even cross‑reference operations.
5. Generate output from IR
Once elaboration and validation passes complete, the IR can be lowered to a target format. For example:
Spice netlist generator: Traverse the IRModule and emit subcircuit definitions (.subckt), port lists, instance lines and .ends. The xDSL IR ensures that ports and nets are properly expanded and mapped.
Visualization or debug output: Use xDSL’s printing facilities to display the IR for debugging or to feed into other analysis tools.
6. Migration strategy
Phase 1 – non‑disruptive integration: Add the xDSL dialect and IR conversion alongside the existing compiler. Implement passes but keep the existing elaborator/validator in place. Provide a command‑line option to output the xDSL IR after parsing for experimentation.
Phase 2 – replace elaboration: Gradually migrate pattern expansion, variable resolution and environment resolution to xDSL passes. Use the existing Elaborator as a wrapper that invokes the pass manager.
Phase 3 – replace validator: Port validator rules to xDSL analysis passes and deprecate the old validator module.
Phase 4 – unify import system: Optionally integrate import resolution into xDSL by adding a pass that loads and merges modules. However, the existing import system can be retained if it provides features not directly related to IR.
Phase 5 – retire dataclass AST for elaboration: Once all transformations operate on the IR, keep the dataclass AST only for front‑end parsing and YAML generation. Downstream passes (simulation, code generation) operate exclusively on the xDSL IR.
Potential Challenges
Dialects and operation definitions: Designing a comprehensive ASDL dialect requires careful modelling of ports, nets, parameters and Spice templates. xDSL provides flexibility but will require new classes and printer/parsers.
Performance considerations: xDSL’s dynamic nature may introduce overhead. Benchmarking and possible C++ MLIR integration should be considered for large designs.
Training and adoption: Developers must become familiar with xDSL concepts (regions, blocks, operations). Clear documentation and examples will ease adoption.
Tooling integration: Existing CLI commands must be updated to use the pass manager. SPICE generation must be rewritten to operate on the IR.
Conclusion
The ASDL compiler currently employs hand‑coded dataclass structures and sequential elaboration logic, which limits extensibility and separation of concerns. Adopting xDSL will introduce a formal IR, a pass infrastructure and the ability to model modules, instances and nets as operations. By defining an ASDL dialect and implementing passes for pattern expansion, variable/environment resolution, import flattening and validation, the compiler can become more modular and easier to extend. A phased migration plan allows incremental adoption without disrupting the existing workflow, ultimately leading to a modern compiler architecture aligned with MLIR/xDSL practices.