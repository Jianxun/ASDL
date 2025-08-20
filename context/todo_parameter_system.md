# ASDL Parameter Resolving System Development Todos

## 🎯 Current Status: Implementation Required (High Priority)

**Priority Level**: **🔥 CRITICAL - BLOCKS IMPORT SYSTEM**

**Decision (2025-08-20)**: Parameter system enhancement must be completed before import system Phase 1 implementation.

## Phase P1: Core Parameter System Enhancement (1-2 days)

### P1.1: Data Structure Updates
- [ ] **Add `variables` field to Module dataclass**
  - [ ] `variables: Optional[Dict[str, Any]] = None`  
  - [ ] Update schema generation to include variables field
  - [ ] Add validation that variables cannot be overridden in instances

### P1.2: Parser Extensions
- [ ] **Support canonical and abbreviated field names**
  - [ ] Parse `parameters` OR `params` → store as `parameters`
  - [ ] Parse `variables` OR `vars` → store as `variables` 
  - [ ] Add validation warnings for using both forms in same module
  - [ ] Update parser tests for dual syntax support

### P1.3: Parameter Override Validation
- [ ] **Implement primitives-only parameter override rule**
  - [ ] Validate parameter overrides only allowed for primitive modules (`spice_template` present)
  - [ ] Generate error for parameter overrides on hierarchical modules (`instances` present)
  - [ ] Generate error for any variable override attempts
  - [ ] Add comprehensive validation tests

### P1.4: Template Generation Enhancement
- [ ] **Update SPICE template substitution**
  - [ ] Support both parameters and variables in template data
  - [ ] Implement variable shadowing of parameters (variables have priority)
  - [ ] Update generator to use enhanced template data
  - [ ] Add tests for template substitution with both field types

### P1.5: Testing & Validation
- [ ] **Comprehensive parameter system tests**
  - [ ] Unit tests for parser dual syntax support
  - [ ] Unit tests for parameter override validation rules
  - [ ] Unit tests for template generation with variables
  - [ ] Integration tests for primitive vs hierarchical parameter handling
  - [ ] Regression tests ensuring existing functionality unchanged

## Phase P2: Advanced Parameter Features (Future)
- [ ] **Parameter hijacking for simulation** (as described in parameter design doc)
- [ ] **Computed variables** with template expressions
- [ ] **Parameter type system integration**
- [ ] **Parameter dependency constraints**

## Implementation Dependencies

### Blocks Import System:
- **Import resolution needs parameter/variable handling** for template substitution
- **Import elaboration must understand parameter semantics** for qualified module references
- **Parameter override validation applies** to both local and imported modules

### Current State Analysis:
- ✅ **Module unified architecture complete** - ready for parameter enhancement
- ✅ **Mutual exclusion validation** - spice_template XOR instances working
- ❌ **Missing `variables` field** - no separation of parameters vs variables
- ❌ **Missing parameter override validation** - no primitives-only enforcement
- ❌ **Limited template substitution** - only uses parameters field

## Success Criteria

### Definition of Done (Phase P1):
1. **`variables` field added** to Module dataclass with schema support
2. **Parser supports dual syntax** for parameters/params and variables/vars
3. **Parameter override validation** prevents overrides on hierarchical modules
4. **Template generation enhanced** to use both parameters and variables
5. **All tests passing** with comprehensive coverage of new functionality
6. **Zero breaking changes** to existing functionality

### Validation Checklist:
- [ ] Existing ASDL files parse without changes
- [ ] Existing SPICE generation output unchanged 
- [ ] New parameter/variable separation works correctly
- [ ] Parameter override validation catches violations
- [ ] Template substitution supports both field types
- [ ] All unit and integration tests pass

## Timeline & Effort Estimation

**Estimated Duration**: 1-2 days total
- **P1.1 Data Structures**: 2-3 hours
- **P1.2 Parser Extensions**: 3-4 hours  
- **P1.3 Override Validation**: 4-5 hours
- **P1.4 Template Enhancement**: 3-4 hours
- **P1.5 Testing**: 4-6 hours

**Risk Factors**: 
- Low risk - well-defined enhancement to existing architecture
- Self-contained changes with clear validation criteria
- Strong foundation from Phase 0 unified architecture

## Context Files Reference
- `doc/elaborator_design/parameter_resolving_system/parameter_resolving_system.md` - Complete design specification
- `context/todo_imports.md` - Blocked pending this implementation
- `src/asdl/data_structures.py` - Target file for Module enhancement