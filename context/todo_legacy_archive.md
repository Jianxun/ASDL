# Project Todo List

## 🔄 **CURRENT SPRINT: MINIMAL VISUALIZER PHASE 2** (READY TO START)

### **🎯 Goal**: Create embeddable, minimal circuit visualizer with named ports
**Architecture**: Functional modules, ~100 lines total, easily tweakable jsPlumb settings

### **Implementation Plan**:

#### **✅ Phase 1: Basic HTML Structure & Canvas Interactions** (COMPLETED)
**Goal**: Create minimal HTML structure with working zoom/pan canvas

- [X] **1.1 Create minimal HTML structure** ✅
  - [X] Strip down `index.html` to bare canvas only (remove sidebar, header, controls, status bar)
  - [X] Simple full-screen canvas div

- [X] **1.2 Zoom and Pan Implementation** ✅ 
  - [X] Initialize jsPlumb with minimal config
  - [X] Mouse wheel zoom with cursor-centered implementation (Community Edition)
  - [X] Mouse drag pan with canvas transform
  - [X] Limit zoom range (0.1x to 3.0x)
  - [X] Proper pan/drag conflict resolution

- [X] **1.3 Simplify CSS to basics** ✅
  - [X] Remove all complex styling, legends, themes
  - [X] Keep only `.circuit-canvas` and `.circuit-node` styles
  - [X] Fixed 60x60px square nodes with simple border

- [X] **1.4 Grid System Implementation** ✅
  - [X] jsPlumb Community Edition grid snap (invisible)
  - [X] Individual draggable element configuration
  - [X] Proper event handling to avoid pan/drag conflicts

**✅ Deliverable**: Fully functional canvas with cursor-centered zoom, smooth panning, grid-snap dragging  
**✅ Test Results**: All functionality working - ready for Phase 2
**📋 Documentation**: Created comprehensive `jsplumb_development_guide.md`

#### **✅ Phase 2: Basic Node Rendering** (COMPLETED)
**Goal**: Render static nodes from enhanced JSON on the zoomable/pannable canvas

**✅ Prerequisites Complete**:
- Enhanced JSON schema with coordinates, dimensions, and node types ✅
- Port-to-device connection directions corrected ✅
- VDD/VSS connections properly included ✅

**Implementation Steps (COMPLETED)**:

- [X] **2.1 Create `createNode(nodeData)` function** ✅
  - [X] Handle three node types: `device`, `port` with `power_supply` model, `port` with `port` model
  - [X] Set position using `nodeData.x, nodeData.y` coordinates
  - [X] Set dimensions using `nodeData.width, nodeData.height`
  - [X] Display `nodeData.label` as text content
  - [X] Apply different styling based on `nodeData.node_type` and `nodeData.model`
  - [X] Add CSS classes: `circuit-node`, `node-{node_type}`, `model-{model}`

- [X] **2.2 Add `loadCircuit(filename)` function** ✅
  - [X] Fetch JSON file using `fetch()` API
  - [X] Parse JSON and store in `this.circuitData`
  - [X] Clear existing nodes from canvas
  - [X] Create nodes using `createNode()` for each node in `nodes` array
  - [X] Add error handling for missing files

- [X] **2.3 Remove test nodes and integrate real data** ✅
  - [X] Remove `createTestNode()` function and its calls
  - [X] Update `init()` to call `loadCircuit('diff_pair_enhanced.json')`
  - [X] Ensure nodes are added to `this.content` container
  - [X] Make all nodes draggable with grid snap using `this.jsPlumbInstance.draggable()`

- [X] **2.4 Add CSS styling for node types** ✅
  - [X] Device nodes: 60×60px, border, centered text
  - [X] Power supply ports: 400×20px, horizontal bar styling
  - [X] Regular ports: 30×30px, smaller border, centered text
  - [X] Add hover effects for better interaction

- [X] **2.5 Test integration** ✅
  - [X] Verify 8 nodes render at correct positions
  - [X] Test zoom/pan functionality with real nodes
  - [X] Verify dragging works with 20px grid snap
  - [X] Check browser console for errors

**Deliverable**: Real circuit nodes visible on canvas at JSON positions, zoom/pan works with nodes  
**Test**: Load `diff_pair_enhanced.json`, see 8 nodes (3 devices + 5 ports), verify they zoom/pan correctly

**Expected Output**:
```
VDD     [============================] ← 400×20px power supply
        
port_in [▢]                           ← 30×30px port
        
R_LOAD  [■]                           ← 60×60px device
        
MN_DP   [■]                           ← 60×60px device
        
M_TAIL  [■]         port_vbn[▢]       ← 60×60px device + 30×30px port
        
        port_out[▢]                   ← 30×30px port
        
VSS     [============================] ← 400×20px power supply
```

#### **✅ Phase 3: Named Port System** (COMPLETED)
**Goal**: Add invisible port anchors to nodes without connections yet

- [X] **3.1 Define port layouts** ✅
  - [X] Create `NODE_PORTS` constant with NMOS, PMOS, resistor port positions
  - [X] Use relative coordinates (0.0-1.0) for anchor positions

- [X] **3.2 Add jsPlumb endpoints** ✅
  - [X] Add named endpoints to nodes using `NODE_PORTS[nodeType]`
  - [X] Use UUID pattern: `${nodeId}-${portName}` (e.g., "M1-G", "M1-D")

**Deliverable**: Nodes have invisible named anchor points that work with zoom/pan  
**Test**: Inspect jsPlumb endpoints, verify UUIDs are correct, zoom in to check positioning

#### **✅ Phase 4: Port-to-Port Connections** (COMPLETED)
**Goal**: Draw connections between named ports using Flowchart connector

- [X] **4.1 Connection rendering** ✅
  - [X] Create `createConnection(connData)` function
  - [X] Connect using UUIDs: `from_node-from_port` → `to_node-to_port`
  - [X] Use Flowchart connector style as specified

- [X] **4.2 Test with realistic circuit** ✅
  - [X] Update JSON to include connections with named ports
  - [X] Test NMOS drain-to-resistor, gate connections, etc.

**Deliverable**: Visible connections between specific ports that work with zoom/pan  
**Test**: Load circuit JSON, see Flowchart-style lines, verify connections scale with zoom

#### **Phase 5: JSON Loading & Integration** (15 minutes)
**Goal**: Dynamic circuit loading and cleanup

- [X] **5.1 Circuit cleanup before reload** (handled by `loadCircuit()`)
- [X] **5.2 Reset zoom/pan state when loading new circuit** (via `reset()` if needed)
- [X] **5.3 Save Layout Button** – Added `#save-layout-btn`, `exportLayout()` downloads updated JSON

**Deliverable**: Can switch between different circuit JSON files  
**Test**: Load different circuits, verify clean transitions, zoom/pan resets properly

#### **Phase 6: Testing & Polish** (15 minutes)
**Goal**: Ensure robust operation and clean code

- [ ] **6.1 Browser compatibility**
  - [ ] Test in Chrome, Firefox, Safari
  - [ ] Verify zoom/pan works consistently
  - [ ] Check for console errors

- [ ] **6.2 Code cleanup**
  - [ ] Remove any leftover verbose code from original app.js
  - [ ] Add minimal comments
  - [ ] Verify total line count is ~100 lines

**Deliverable**: Production-ready minimal visualizer  
**Test**: Works reliably across browsers, embeddable in other pages

### **Success Criteria**:
- ✅ **Minimal**: HTML+CSS+JS under 200 lines total
- ✅ **Embeddable**: No UI chrome, just circuit canvas
- ✅ **Named ports**: NMOS G/S/D/B connections work correctly
- ✅ **Zoom/Pan**: Smooth, doesn't break connections
- ✅ **Flowchart**: Connector style as specified
- ✅ **JSON-driven**: Complete circuit definition in JSON

**Estimated Total Time: 2 hours**

---

## 🎉 **VISUALIZATION PROTOTYPE COMPLETED ✅** (MAJOR MILESTONE - ARCHIVED)

### **🚀 Ready for Next Sprint: Frontend Development**
**FOUNDATION COMPLETE**: The ASDL-to-JSON extraction pipeline is now production-ready with full differential pair support

**✅ Major Achievement Summary**:
- **Parser Bug Discovery & Resolution** ✅
- **ASDL File Validation & Correction** ✅  
- **Hierarchy Extractor Implementation** ✅
- **Node-to-Node Connection Mapping** ✅
- **Differential Net Preservation** ✅
- **Complete Backend Pipeline** ✅

**Next Phase**: Build HTML/CSS/JavaScript frontend using jsPlumb for interactive circuit visualization

## 🎉 **PHASE 1: STATIC SCHEMATIC RENDERER COMPLETED ✅** (MAJOR MILESTONE)

### **✅ COMPLETE FRONTEND VISUALIZATION SYSTEM DELIVERED**
- [X] Create HTML page structure (`prototype/visualization/index.html`) ✅
- [X] Implement CSS styling for circuit components (`prototype/visualization/style.css`) ✅
- [X] Build JavaScript JSON loader and jsPlumb integration (`prototype/visualization/app.js`) ✅
- [X] Render nodes as draggable HTML elements ✅
- [X] Draw connections using jsPlumb with differential/single styling ✅
- [X] Test with `diff_pair.json` data ✅
- [X] **BONUS**: Professional UI with sidebar, legend, controls, and status tracking ✅

**🚀 PRODUCTION READY**: Complete frontend visualization system committed to repository

## Next Session: **Phase 2: Interactive Features Enhancement**

### **Phase 2: Interactive Features** 
- [ ] Implement node dragging with connection preservation
- [ ] Add pan and zoom functionality to canvas
- [ ] Create hover tooltips for components and connections
- [ ] Add visual distinction for differential vs single-ended connections

### **Phase 3: Advanced Visualization**
- [ ] Implement component styling based on model type (nmos, pmos, resistor, etc.)
- [ ] Add connection labels showing net names
- [ ] Create legend explaining symbols and connection types
- [ ] Add export functionality (PNG/SVG)

## 🎉 **ELABORATOR IMPLEMENTATION COMPLETED ✅** (MAJOR MILESTONE)

### **🚀 Ready for Next Sprint: SPICEGenerator Refactoring**
**FOUNDATION COMPLETE**: The `Elaborator` is now production-ready with comprehensive pattern expansion capabilities

**✅ Major Achievement Summary**:
- **13/13 elaborator tests passing** ✅
- **Complete PatternExpander replacement** ✅  
- **Enhanced diagnostic system** ✅
- **Order-sensitive pattern expansion** ✅
- **Comprehensive instance mapping expansion** ✅
- **Mixed pattern detection and validation** ✅

**Next Phase**: Refactor `SPICEGenerator` to consume elaborated ASDL files and deprecate `PatternExpander`

## Previous Sprint - Validation & Quality Enhancements (COMPLETED)

### 🎉 **CRITICAL PARAMETER PROPAGATION BUG FIX COMPLETED ✅**
- [X] **Critical Module Instance Parameter Propagation Bug Fix** ✅

**Critical Achievement**: Module instances now correctly pass parameters to subcircuit calls in SPICE output. The `two_stage_ota` example now generates `X_FIRST_STAGE ... M={M_first_stage}` instead of missing the parameter entirely. This fixes a fundamental bug that broke hierarchical parameterization in complex analog designs.

### 🎉 **NET DECLARATION VALIDATION COMPLETED ✅**
- [X] **Net Declaration Validation Feature** ✅

**Technical Achievement**: SPICEGenerator now provides intelligent connectivity validation that catches undeclared nets while maintaining robust netlisting functionality. This addresses the specific issue identified in `two_stage_ota.yml` where `out_n` and `out_<p,n>` nets were used but not declared.

### 🎉 **PARSER STABILIZATION & TEST SUITE HARDENING COMPLETED ✅**
- [X] **Task: Stabilize test suite after `Locatable` refactoring** ✅

### 🎉 **CRITICAL PATTERN EXPANSION BUG FIX COMPLETED ✅**
- [X] **Major Circuit Correctness Bug Fix** ✅

**Critical Achievement**: Fixed bug that completely broke differential amplifier functionality. Pattern expansion now correctly routes signals to differential pairs and other multi-instance circuits.

### 🎉 **PORT ORDER CANONICAL COMPLIANCE COMPLETED ✅**
- [X] **Critical Bug Fix: SPICE Port Order** ✅

**Technical Achievement**: SPICE `.subckt` declarations now follow the canonical order defined in the ASDL YAML `ports:` section, ensuring consistency and predictability across all generated netlists.

### 🎉 **UNUSED COMPONENT VALIDATION COMPLETED ✅**
- [X] **Core Unused Validation Feature** ✅

**Technical Achievement**: SPICEGenerator now provides intelligent validation that helps developers identify dead code while maintaining robust netlisting functionality.

## Current Sprint: **THOROUGH DATA STRUCTURE REFACTOR ✅ COMPLETE**

### **🎉 COMPLETE LEGACY REMOVAL & ARCHITECTURE CLEANUP ✅**
- [X] **Phase 1: PrimitiveType Enum** ✅
- [X] **Phase 2: Universal Metadata Field** ✅
- [X] **Phase 3: Internal Nets Field** ✅
- [X] **Phase 4: Simplified DeviceModel** ✅
- [X] **Phase 5: Serialization Separation** ✅

**🎯 PRODUCTION READY**: Clean architecture, 34/34 data structure tests passing ✅

## Next Sprint: Linter & Compiler Architecture Refactoring
- [X] **Phase 1: Parser Refactoring** ✅
- [X] **Phase 2: Full Location Tracking** ✅
- [X] **Phase 3: Foundation** ✅
- [X] **Phase 4: Diagnostic System Foundation** ✅
- [X] **Phase 5: Elaboration & Analysis Pipeline** ✅ **COMPLETE**
- [ ] **Phase 5: Parser Hardening (TDD)**
  - [X] **Roadblock Resolved**: Type-safe access to `ruamel.yaml` location data is working. ✅
  - [X] Implement and test `P200`: Unknown Top-Level Section (Warning). ✅
  - [ ] Implement and test `P102`: Missing Required Section.
  - [ ] Implement and test `P103`: Invalid Section Type.
  - [ ] Implement and test `P201`: Unknown Field (Warning).
- [ ] **Phase 6: SPICEGenerator Refactoring Pipeline** (NEXT PRIORITY)
  - [ ] **Step 4: Refactor SPICEGenerator to use Elaborator**
    - [ ] Update generator to consume elaborated ASDLFile from Elaborator.
    - [ ] Remove all pattern expansion logic from SPICEGenerator.
    - [ ] Pass parameter strings through as-is.
    - [ ] Refactor generator test suite to use elaborated fixtures.
    - [ ] Verify all existing functionality preserved.
  - [ ] **Step 5: Deprecate PatternExpander**
    - [ ] Delete `src/asdl/expander.py` and its associated tests.
    - [ ] Remove parameter resolution logic from `SPICEGenerator`.
    - [ ] Update any remaining references to use Elaborator.
- [ ] **Phase 5: Tooling Back-Ends**
  - [ ] Create Linter entry point script (`scripts/asdl_linter.py`)

## Backlog: Advanced Validation & User Experience

### **Testing & Refinements**
- [ ] Thoroughly test `serialization.py` module

### **Enhanced Validation Features** (NEW PRIORITY)
- [ ] **Cross-Reference Validation**
  - [ ] Detect and warn about circular dependencies between modules
  - [ ] Validate parameter references (undefined parameters used)
  - [ ] Check for orphaned nets (declared but never connected)
  - [ ] Validate port width consistency in pattern expansions
- [ ] **Design Rule Checking (DRC)**
  - [ ] Basic electrical rules (no floating inputs/outputs)
  - [ ] Port direction consistency checking
  - [ ] Parameter range validation
  - [ ] Device constraint validation (W/L ratios, etc.)
- [ ] **Parameter Resolution (DEFERRED)**
  - [ ] Implement robust parameter resolution in `Elaborator`.
  - [ ] Handle hierarchical scope and expressions.
  - [ ] Add diagnostic reporting for undefined parameters and circular dependencies.

### **User Experience Enhancements**
- [ ] **Improved Error Messages**
  - [ ] Line number references in YAML files for errors/warnings
  - [ ] Suggestion system for common mistakes
  - [ ] Context-aware error descriptions
  - [ ] Color-coded warning levels (info, warning, error)
- [ ] **Documentation Generation**
  - [ ] Auto-generate circuit documentation from ASDL designs
  - [ ] HTML documentation with cross-references
  - [ ] Dependency graphs and usage maps
  - [ ] Parameter sensitivity analysis

## PHASE 5: Pattern Expansion & Advanced Features (COMPLETED)

### 🎉 **PHASE 5 COMPLETED ✅** (Pattern Expansion & Advanced Features + Test Expectation Updates)
**PERFECT TEST STATUS ACHIEVED**: 131/131 tests passing ✅

### 🎉 **TEST EXPECTATION REFACTORING COMPLETED ✅**
- [X] **Complete Test Architecture Update** ✅

**✅ Pre-Release Achievement**: All tests now validate the current hierarchical subcircuit architecture

### 🎉 **PATTERN EXPANSION SYSTEM COMPLETED ✅**
- [X] **Pattern Expansion Rules Documentation** ✅
- [X] **CRITICAL MAPPING FORMAT CORRECTION** ✅
- [X] **SCHEMA v0.5 REFINEMENT & LANGUAGE DOCUMENTATION** ✅
- [X] **Pattern Expansion System Implementation** ✅

## Current Sprint: **GENERATOR REFACTORING COMPLETED ✅**

### 🎉 **MAJOR MILESTONE ACHIEVED** 
**SPICEGenerator Fully Restored and Modernized**

- [X] Extract validation logic from SPICEGenerator using TDD approach ✅
- [X] Implement ASDLValidator with port mapping validation ✅
- [X] Implement ASDLValidator with net declaration validation ✅  
- [X] Implement ASDLValidator with unused components validation ✅
- [X] Remove all validation logic from SPICEGenerator (clean separation) ✅
- [X] **Fix SPICEGenerator data structure compatibility issues** ✅
  - [X] Fix DeviceType → PrimitiveType import ✅
  - [X] Fix DeviceModel method calls (parameters, doc, device_line) ✅
  - [X] Update method signatures to match new data structures ✅
  - [X] Remove deprecated DEVICE_FORMATS template system ✅
  - [X] Implement pure device_line approach with parameter substitution ✅
- [X] **Create end-to-end integration tests** ✅
  - [X] Simple resistor pipeline test ✅
  - [X] Complex diff_pair_nmos pipeline test with pattern expansion ✅
- [X] **Test generator with real ASDL files** ✅
- [X] **Update fixture files to new schema** ✅
- [X] **Update netlist_asdl.py script to modern pipeline** ✅
  - [X] Replace PatternExpander with Elaborator ✅
  - [X] Fix parser tuple handling ✅  
  - [X] Test script with real ASDL files ✅

## Backlog
- [ ] Enhanced validation features
  - [ ] Cross-reference validation between modules
  - [ ] Circular dependency detection
  - [ ] Parameter type validation
- [ ] Generator improvements
  - [ ] Better error handling for malformed ASDL files
  - [ ] Support for more SPICE device types
  - [ ] Optimization for large hierarchical designs
- [ ] Documentation updates
  - [ ] Update README with new validation pipeline
  - [ ] Add examples showing validator usage
  - [ ] Document migration from old validation approach

## Completed Tasks
- [X] **MAJOR MILESTONE**: Complete elaborator implementation with 13/13 tests passing
- [X] **MAJOR MILESTONE**: Data structure refactoring with 34/34 tests passing  
- [X] **MAJOR MILESTONE**: Parser implementation with 23/23 tests passing
- [X] **MAJOR MILESTONE**: Validation extraction with 6/6 validator tests passing
- [X] Implement comprehensive pattern expansion system
- [X] Add location tracking and diagnostics to parser
- [X] Create structured diagnostic system
- [X] Refactor data structures for clean architecture
- [X] Remove legacy code and backward compatibility
- [X] Implement TDD approach for validation methods
- [X] Extract all validation logic from generator (214 lines removed)
- [X] Create comprehensive test suite for validator
- [X] Clean separation of concerns between validation and generation

## Current Sprint: **GENERATOR TEST SUITE REFACTORING ✅ COMPLETE**

### **🎉 COMPREHENSIVE GENERATOR TEST CLEANUP COMPLETED ✅**
- [X] **Legacy Validation Test Removal** ✅ - Removed 1,567 lines of obsolete tests
- [X] **Comprehensive Method Coverage** ✅ - 8 new unit tests covering all generation methods
- [X] **PySpice Integration Testing** ✅ - SPICE validation with parse-back verification
- [X] **Parser API Compatibility** ✅ - Updated all tests for new parser tuple return format
- [X] **Integration Test Organization** ✅ - Moved end-to-end tests to proper directory

**🎯 PRODUCTION READY**: Modern test suite focused on generation functionality with comprehensive coverage

## Previous Sprint: **ENHANCED ERROR REPORTING ✅ COMPLETE**

### **🎉 ENHANCED DIAGNOSTIC SYSTEM COMPLETED ✅**
- [X] **Line/Column Error Reporting Enhancement** ✅
- [X] **Locatable String Formatting** ✅
- [X] **Diagnostic Pipeline Integration** ✅
- [X] **Real-world Testing with two_stage_ota.yml** ✅

**🎯 PRODUCTION READY**: Enhanced error reporting with precise location information for all ASDL debugging

## Next Sprint: Advanced Validation & User Experience

### **Enhanced Validation Features** (NEW PRIORITY)
- [ ] **Cross-Reference Validation**
  - [ ] Detect and warn about circular dependencies between modules
  - [ ] Validate parameter references (undefined parameters used)
  - [ ] Check for orphaned nets (declared but never connected)
  - [ ] Validate port width consistency in pattern expansions
- [ ] **Design Rule Checking (DRC)**
  - [ ] Basic electrical rules (no floating inputs/outputs)
  - [ ] Port direction consistency checking
  - [ ] Parameter range validation
  - [ ] Device constraint validation (W/L ratios, etc.)

## Current Sprint: **INTEGRATION TEST FRAMEWORK ENHANCEMENT ✅ COMPLETE**

### **🎉 INTEGRATION TEST FRAMEWORK & DEVICE MODEL IMPROVEMENTS COMPLETED ✅**
- [X] **Resolve Integration Test Failures** ✅
- [X] **Implement Case-Insensitive Error Detection** ✅
- [X] **Fix Device Model Parameterization** ✅
- [X] **Create Fully Parameterized Device Templates** ✅

**Technical Achievement**: Successfully enhanced the integration test framework and device models by:
1. **Schema Migration**: Updated `inverter.yml` from legacy `design_info` to current `file_info` format
2. **Device Type Fixes**: Corrected primitive types from `nmos`/`pmos` to `pdk_device` 
3. **Missing File Generation**: Created `inverter_netlist.spice` using the ASDL pipeline
4. **Infrastructure Setup**: Created `tests/integration/results/` directory for test outputs
5. **Case-Insensitive Error Detection**: Enhanced test framework to catch all error variants
6. **Device Model Parameterization**: Added proper SPICE parameter definitions (M, nf, L, W)
7. **Template Parameterization**: Made device_line fully parameterized with placeholders
8. **NgSpice Clean Execution**: Eliminated all SPICE simulation errors and warnings
9. **End-to-End Validation**: Confirmed complete pipeline functionality

**🎯 PRODUCTION READY**: Complete test suite with 82/82 tests passing including 8/8 integration tests with clean NgSpice execution ✅

### **Key Improvements Made**
- **Error Detection**: `assert "error" not in combined_output.lower()` - catches all error variants
- **Device Templates**: `L={L} W={W} nf={nf} M={M}` - fully parameterized with proper `.param` declarations
- **PDK Expressions**: Realistic area/perimeter calculations with proper parameter dependencies
- **Test Robustness**: Integration tests now validate actual SPICE simulation success, not just file existence