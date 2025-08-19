# ASDL Import System Implementation Plan

## Overview

This document outlines the implementation plan for the unified import strategy defined in `asdl_import_dependency_management.md`. The current ASDL implementation is single-file only and requires substantial infrastructure additions to support the import system and unified module architecture.

**Note**: The 3-layer abstraction (PDK primitives → Unit devices → Design logic) described in the dependency management document is a **practice guideline** for organizing analog designs, not a compiler enforcement. The core distinction enforced by the compiler is simply:
- **Primitive modules**: Have `spice_template`, render as inline SPICE 
- **Hierarchical modules**: Have `instances`, render as `.subckt` definitions

## Current State Analysis

### ✅ **Existing Strengths**
- Well-structured data model with `ASDLFile`, `Module` classes
- Robust parser with location tracking and diagnostic reporting
- Comprehensive elaborator for pattern expansion (`<>` and `[]` syntax)
- Working SPICE generator with hierarchical subcircuit support
- Parameter resolution framework (basic implementation)

### 🔴 **Missing Infrastructure**
- **No import system**: No `imports` section support in parser or data structures
- **Single-file limitation**: No multi-file dependency resolution
- **No library registry**: No mechanism for `library.filename` → file path resolution
- **No qualified names**: No support for `alias.module_name` references
- **No PDK integration**: Missing `.include` generation for PDK primitives
- **Redundant data structures**: `DeviceModel` and `Module` have significant overlap

## Implementation Strategy

### **Phase 0: Data Structure Unification (Foundation)**

#### **0.1 Eliminate DeviceModel/Module Redundancy**
**File**: `src/asdl/data_structures.py`

The current separation of `DeviceModel` and `Module` creates unnecessary complexity. Both represent reusable components with ports, parameters, and implementation details. We unify them into a single `Module` class:

```python
@dataclass
class Module(Locatable):
    """Unified representation for both primitives and hierarchical circuits"""
    doc: Optional[str] = None
    ports: Optional[Dict[str, Port]] = None
    parameters: Optional[Dict[str, Any]] = None
    
    # MUTUALLY EXCLUSIVE: Either primitive OR hierarchical
    spice_template: Optional[str] = None              # Primitive modules only
    instances: Optional[Dict[str, Instance]] = None   # Hierarchical modules only
    
    # Additional fields
    internal_nets: Optional[List[str]] = None
    pdk: Optional[str] = None                        # For PDK primitive modules
    metadata: Optional[Metadata] = None

@dataclass
class ImportDeclaration:
    """Represents a single import: alias: library.filename[@version]"""
    alias: str                    # Local alias for imported file
    qualified_source: str         # library.filename format
    version: Optional[str] = None # Optional @1.2.0 version tag
    
@dataclass
class ASDLFile:
    file_info: FileInfo
    imports: Optional[Dict[str, ImportDeclaration]] = None  # NEW
    modules: Dict[str, Module]     # UNIFIED: No separate models section
    metadata: Optional[Metadata] = None
```

**Key Changes**:
- **Remove `models` section entirely** - everything is a module
- **Add `spice_template` field** to `Module` for primitive implementations
- **Enforce mutual exclusion**: Modules have either `spice_template` OR `instances`
- **Simplified validation**: Single code path for all components

### **Phase 1: Core Import Infrastructure (MVP)**

#### **1.1 Updated Data Structure Changes**
**File**: `src/asdl/data_structures.py`

The unified structure above eliminates the `DeviceModel` class entirely. All components are represented as modules with different characteristics:

**Primitive Modules** (current "models"):
```yaml
modules:
  nfet_03v3:
    ports:
      D: {dir: in_out, type: voltage}
      G: {dir: in, type: voltage}  
      S: {dir: in_out, type: voltage}
      B: {dir: in_out, type: voltage}
    parameters: {L: 0.28u, W: 3u, M: 1}
    spice_template: MN {D} {G} {S} {B} nfet_03v3 L={L} W={W} m={M}
    pdk: gf180mcu
    # No instances field - this is primitive
```

**Hierarchical Modules**:
```yaml
modules:
  current_mirror:
    ports:
      ref: {dir: in, type: voltage}
      out: {dir: out, type: voltage}
    instances:
      M1: {model: nfet_03v3, mappings: {...}}
      M2: {model: nfet_03v3, mappings: {...}}
    # No spice_template field - this is hierarchical
```

#### **1.2 Parser Extensions**
**File**: `src/asdl/parser.py`

```python
def _parse_imports(self, data: Any, diagnostics: List[Diagnostic], 
                  file_path: Optional[Path]) -> Dict[str, ImportDeclaration]:
    """Parse imports section with validation"""
    
def _validate_import_syntax(self, alias: str, qualified_source: str, 
                          location: Locatable) -> List[Diagnostic]:
    """Validate library.filename format and alias naming"""

def _parse_modules(self, data: Any, diagnostics: List[Diagnostic], 
                  file_path: Optional[Path]) -> Dict[str, Module]:
    """Parse unified modules section (replaces separate models/modules parsing)"""
    
def _validate_module_exclusivity(self, module_data: Dict, 
                               location: Locatable) -> List[Diagnostic]:
    """Ensure modules have either spice_template OR instances, not both"""
```

**Changes Required**:
- Add `imports` to allowed top-level sections  
- **Remove `models` from allowed sections completely** (breaking change - no compatibility)
- Parse `alias: library.filename[@version]` format
- **Unified module parsing** - handle both primitive and hierarchical in single code path
- **Mutual exclusion validation** - `spice_template` XOR `instances`
- Generate diagnostics for malformed imports and invalid module definitions

#### **1.3 Library Registry System**
**File**: `src/asdl/library_registry.py` (new)

```python
class LibraryRegistry:
    """Manages library discovery and path resolution"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.library_paths: Dict[str, Path] = {}
        self.load_config(config_path)
    
    def resolve_library_path(self, library_name: str) -> Optional[Path]:
        """Resolve library name to filesystem path"""
        
    def resolve_qualified_source(self, qualified_source: str) -> Path:
        """Convert library.filename to absolute file path"""
        # library.filename → library_path/filename.asdl
```

**Configuration Format** (`asdl.lib.yaml`):
```yaml
libraries:
  gf180mcu_pdk: /shared/pdks/gf180mcu_pdk
  gf180mcu_std_tiles: /shared/pdks/gf180mcu_std_tiles
  analog_ip: ./libs/analog_ip
```

#### **1.4 Import Resolution Engine**
**File**: `src/asdl/import_resolver.py` (new)

```python
class ImportResolver:
    """Resolves imports and merges dependencies into single ASDLFile"""
    
    def __init__(self, library_registry: LibraryRegistry):
        self.registry = library_registry
        self.resolved_cache: Dict[str, ASDLFile] = {}
    
    def resolve_imports(self, asdl_file: ASDLFile) -> Tuple[ASDLFile, List[Diagnostic]]:
        """Resolve all imports and merge into self-contained design"""
        
    def _resolve_single_import(self, import_decl: ImportDeclaration) -> ASDLFile:
        """Load and parse a single imported file"""
        
    def _merge_imports(self, base_file: ASDLFile, 
                      imports: Dict[str, ASDLFile]) -> ASDLFile:
        """Merge imported modules with namespace prefixing"""
        
    def _detect_circular_imports(self, dependency_chain: List[str]) -> bool:
        """Detect circular import dependencies"""
```

**Key Features**:
- Recursive import resolution with circular dependency detection
- Namespace management for imported modules (unified namespace)
- Caching to avoid reloading same files
- Comprehensive error reporting for missing files/modules

#### **1.5 Elaborator Integration**
**File**: `src/asdl/elaborator.py`

```python
class Elaborator:
    def __init__(self, import_resolver: ImportResolver):
        self.import_resolver = import_resolver
    
    def elaborate(self, asdl_file: ASDLFile) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """Two-stage elaboration: imports first, then patterns"""
        diagnostics = []
        
        # PHASE 1: Import resolution (NEW)
        if asdl_file.imports:
            resolved_file, import_diagnostics = self.import_resolver.resolve_imports(asdl_file)
            diagnostics.extend(import_diagnostics)
            if import_diagnostics and any(d.severity == DiagnosticSeverity.ERROR for d in import_diagnostics):
                return None, diagnostics
        else:
            resolved_file = asdl_file
            
        # PHASE 2: Pattern expansion (EXISTING)
        elaborated_file = replace(resolved_file, modules={})
        for name, module in resolved_file.modules.items():
            elaborated_module, module_diagnostics = self._elaborate_module(module)
            diagnostics.extend(module_diagnostics)
            elaborated_file.modules[name] = elaborated_module
            
        return elaborated_file, diagnostics
```

### **Phase 2: Enhanced Module References**

#### **2.1 Qualified Name Resolution**
**File**: `src/asdl/data_structures.py`

```python
@dataclass
class Instance(Locatable):
    model: str  # Now supports both local names and qualified names (alias.module)
    mappings: Dict[str, str]
    # ... existing fields
    
    def get_qualified_model(self, imports: Dict[str, ImportDeclaration]) -> str:
        """Resolve alias.module to fully qualified name"""
        if '.' in self.model:
            alias, module_name = self.model.split('.', 1)
            if alias in imports:
                return f"{imports[alias].qualified_source}.{module_name}"
        return self.model
```

#### **2.2 Generator Updates**
**File**: `src/asdl/generator.py`

```python
class SPICEGenerator:
    def generate(self, asdl_file: ASDLFile) -> str:
        """Generate SPICE from fully elaborated (import-resolved) design"""
        # By Phase 1, all imports are resolved into single file
        # Existing generation logic works unchanged
        
        # NEW: Add PDK include generation
        pdk_includes = self._generate_pdk_includes(asdl_file)
        
    def _generate_pdk_includes(self, asdl_file: ASDLFile) -> List[str]:
        """Generate .include statements for PDK modules"""
        includes = []
        used_pdks = set()
        
        for module in asdl_file.modules.values():
            if module.pdk and module.pdk not in used_pdks:
                includes.append(f'.include "{module.pdk}_models.ngspice"')
                used_pdks.add(module.pdk)
                
        return includes
        
    def _generate_module_spice(self, module: Module, module_name: str) -> str:
        """Generate SPICE for unified module (primitive or hierarchical)"""
        if module.spice_template:
            # Primitive module - render as inline SPICE using template
            return self._generate_inline_spice(module, module_name)
        elif module.instances:
            # Hierarchical module - render as .subckt definition 
            return self._generate_subcircuit(module, module_name)
        else:
            raise ValueError(f"Module {module_name} has neither spice_template nor instances")
```

### **Phase 3: Optional Module Classification (Practice Guidelines)**

#### **3.1 Module Classification System (Optional)**
**File**: `src/asdl/data_structures.py`

The unified `Module` structure supports optional classification for practice guidelines, but this is not enforced by the compiler:

```python
class ModuleType(Enum):
    """Optional classification for design practice guidelines (not enforced)"""
    PRIMITIVE = "primitive"              # Has spice_template
    HIERARCHICAL = "hierarchical"        # Has instances
    # Optional sub-classifications for practice guidelines:
    PDK_PRIMITIVE = "pdk_primitive"      # Primitive with pdk field
    SPICE_PRIMITIVE = "spice_primitive"  # Primitive without pdk field

def classify_module(module: Module) -> ModuleType:
    """Classify module type for tooling/linting (not compiler enforcement)"""
    if module.spice_template:
        return ModuleType.PRIMITIVE
    elif module.instances:
        return ModuleType.HIERARCHICAL
    else:
        raise ValueError("Module has neither spice_template nor instances")
```

#### **3.2 Optional Practice Guideline Validation**
**File**: `src/asdl/linting.py` (new - separate from core validator)

```python
class DesignPracticeLinter:
    """Optional linting for design practice guidelines (not errors)"""
    
    def lint_unit_device_practices(self, module: Module) -> List[Diagnostic]:
        """Suggest unit device best practices (warnings, not errors)"""
        # Optional validation for 3-layer architecture guidelines
        # These are warnings/suggestions, not compilation errors
        
    def lint_design_organization(self, asdl_file: ASDLFile) -> List[Diagnostic]:
        """Suggest design organization best practices"""
        # Optional guidance for following 3-layer practice guidelines
```

### **Phase 4: Advanced Features**

#### **4.1 Parameterized Imports**
```python
# Support for technology-parameterized imports
imports:
  std_devices: ${technology}_std_tiles.devices
  
parameters:
  technology: gf180mcu  # Can be overridden at testbench level
```

#### **4.2 Version Management**
```python
# Import with version constraints
imports:
  amplifiers: analog_ip.amplifiers@1.2.0
  primitives: gf180mcu_pdk.primitives@>=2.0.0
```

## File Modification Summary

### **New Files Required**
- `src/asdl/library_registry.py` - Library discovery and path resolution
- `src/asdl/import_resolver.py` - Import resolution and merging engine
- `tests/unit_tests/imports/` - Comprehensive import system tests

### **Modified Files**
- `src/asdl/data_structures.py` - **Unify Module/DeviceModel + add import structures**
- `src/asdl/parser.py` - **Unified module parsing + imports section**
- `src/asdl/elaborator.py` - Integrate import resolution phase
- `src/asdl/generator.py` - **Handle unified modules (primitive vs hierarchical) + PDK include generation**
- `src/asdl/validator.py` - Add core module validation (spice_template XOR instances)
- `src/asdl/linting.py` - Optional practice guideline validation (new file)

### **Configuration Files**
- `asdl.lib.yaml` - Library registry configuration

## Implementation Phases

### **Phase 0 Deliverables (Breaking Refactor)**
- [ ] **Delete DeviceModel class entirely** - aggressive cleanup
- [ ] **Remove `models` section completely** - no backward compatibility
- [ ] **Rewrite parser** - single unified module parsing path only
- [ ] **Rewrite generator** - unified module handling (primitive vs hierarchical)
- [ ] **Update all existing ASDL files** - migrate `models` → `modules` with `spice_template`

### **Phase 1 Deliverables (MVP)**
- [ ] Basic import syntax: `alias: library.filename`
- [ ] Library registry with `asdl.lib.yaml` support
- [ ] Single-level import resolution (no transitive imports)
- [ ] Qualified module references: `alias.module_name`
- [ ] Integration with existing elaboration pipeline

### **Phase 2 Deliverables**
- [ ] Transitive import resolution with circular detection
- [ ] Enhanced error diagnostics for import failures
- [ ] PDK integration with `.include` generation
- [ ] Core primitive vs hierarchical validation

### **Phase 3 Deliverables**
- [ ] Parameterized imports with variable substitution
- [ ] Version constraint support
- [ ] Optional practice guideline linting (3-layer architecture suggestions)
- [ ] Cross-technology design validation

## Breaking Changes (MVP Phase)

**🔥 Aggressive Refactor**: Since ASDL is still in MVP phase, we can make clean breaking changes for better architecture.

**Breaking Changes**:
- **Delete `DeviceModel` class completely** - no backward compatibility
- **Remove `models` section** - parser will reject files with `models` section
- **All existing ASDL files must be updated** - migrate `models` → `modules` with `spice_template`
- **Generator API changes** - unified module handling replaces separate model/module logic

**Migration Required**:
```yaml
# OLD FORMAT (will break)
models:
  nfet_03v3:
    type: pdk_device
    ports: [D, G, S, B]
    device_line: MN {D} {G} {S} {B} nfet_03v3

# NEW FORMAT (required)
modules:
  nfet_03v3:
    ports:
      D: {dir: in_out, type: voltage}
      G: {dir: in, type: voltage}
    spice_template: MN {D} {G} {S} {B} nfet_03v3
    pdk: gf180mcu
```

**Benefits of Breaking Changes**:
- **Clean architecture** - single unified abstraction
- **Simplified codebase** - remove redundant classes and parsing logic
- **Better foundation** - solid base for import system
- **Future-proof design** - extensible module classification system

## Testing Strategy

### **Unit Tests**
- **Module unification**: Unified parsing and validation logic (spice_template XOR instances)
- **Import syntax**: Parsing and validation of import declarations
- **Library registry**: Path resolution and configuration loading
- **Import resolution**: Algorithm correctness and circular dependency detection
- **Namespace management**: Collision handling and qualified name resolution

### **Integration Tests**
- **Primitive vs hierarchical**: Correct SPICE generation (inline vs .subckt)
- **Multi-file designs**: End-to-end compilation with imports
- **Cross-library references**: Qualified module name resolution
- **SPICE generation**: Primitive modules render inline, hierarchical modules render as subcircuits
- **Error handling**: Comprehensive diagnostic quality for new architecture

### **Example Test Cases**
```yaml
# Unified module test (clean new architecture)
modules:
  # Primitive module (clean new format)
  nfet_03v3:
    ports:
      D: {dir: in_out, type: voltage}
      G: {dir: in, type: voltage}
    spice_template: MN {D} {G} {S} {B} nfet_03v3
    pdk: gf180mcu
    
  # Hierarchical module
  test_design:
    instances:
      M1: {model: nfet_03v3, mappings: {...}}

# Import test with unified modules
imports:
  pdk: gf180mcu_pdk.primitives
  
modules:
  test_design:
    instances:
      M1: {model: pdk.nfet_03v3, mappings: {...}}
```

## Implementation Path

### **Step 0**: Aggressive Breaking Refactor (clean slate)
- Delete `DeviceModel` class and all related code
- Remove `models` section from parser completely
- Update all existing ASDL files to new unified format
- Rewrite generator for unified module handling

### **Step 1**: Enable imports in parser (builds on clean foundation)
### **Step 2**: Create library registry and basic resolution  
### **Step 3**: Support qualified module references
### **Step 4**: Add optional practice guideline linting
### **Step 5**: Advanced features (parameterized imports, versioning)

This approach prioritizes clean architecture over compatibility, creating a solid foundation for the import system without legacy complexity.

## Key Benefits of Unified Architecture

### **Conceptual Clarity**
- **Single abstraction**: Everything is a module (primitive or hierarchical)
- **Clear semantics**: `spice_template` = inline SPICE, `instances` = .subckt definition
- **Uniform import system**: `alias.module_name` works for all components
- **Practice guidelines**: 3-layer architecture remains as design guidance, not enforcement

### **Implementation Simplification**  
- **Single parser path**: One code path instead of two separate parsers
- **Unified generator**: Handle all modules with consistent primitive vs hierarchical logic
- **Simpler validation**: Single validation framework focusing on core requirements
- **Reduced complexity**: Fewer data structures and relationships to maintain

### **Future Extensibility**
- **Module classification**: Easy to add new module types (behavioral, extracted, etc.)
- **Consistent imports**: Same import mechanism for all component types  
- **Better tooling support**: Unified data model enables better IDE integration
- **Optional linting**: Practice guidelines can be enforced via separate linting tools