# Environment Variable Support Implementation

## Overview
Implement environment variable support in ASDL parameters using `${VAR}` syntax. Environment variables are resolved during elaboration phase and integrated with existing parameter resolution pipeline.

## Design Decisions ✅
- **Syntax**: Only `${VAR}` format supported in parameter values
- **Resolution**: At elaboration time, integrated with parameter resolution
- **Error Handling**: E0501 for missing env vars, E0502 for invalid format
- **No Defaults**: Fail fast for missing environment variables
- **Integration**: No changes to generator logic needed

## Implementation Phases

### Phase 1.3.1: Extend VariableResolver
**Status**: Ready to Start  
**Priority**: High  
**Estimated Effort**: 1-2 hours

**Tasks**:
- [ ] Add `resolve_environment_variables()` method to `VariableResolver`
- [ ] Implement `${VAR}` syntax validation (strict format only)
- [ ] Add environment variable resolution logic
- [ ] Integrate with existing parameter resolution flow
- [ ] Add diagnostic code generation (E0501, E0502)

**Files to Modify**:
- `src/asdl/elaborator/variable_resolver.py`
- `src/asdl/diagnostics.py` (add new error codes)

**Success Criteria**:
- [ ] Method resolves `${VAR}` to environment variable values
- [ ] Invalid formats emit appropriate error diagnostics
- [ ] Missing environment variables emit E0501 with parameter context
- [ ] Integration with existing parameter resolution works correctly

### Phase 1.3.2: Elaborator Integration
**Status**: Blocked by Phase 1.3.1  
**Priority**: High  
**Estimated Effort**: 30 minutes

**Tasks**:
- [ ] Ensure environment variable resolution happens during elaboration
- [ ] Verify resolution order: Environment → Parameters → Instance Variables
- [ ] Test integration with existing elaborator pipeline

**Files to Modify**:
- `src/asdl/elaborator/elaborator.py` (if needed)

**Success Criteria**:
- [ ] Environment variables resolved before parameter substitution
- [ ] No changes needed to existing elaborator logic
- [ ] Pipeline maintains existing behavior for non-environment parameters

### Phase 1.3.3: Testing and Validation
**Status**: Blocked by Phase 1.3.2  
**Priority**: High  
**Estimated Effort**: 1-2 hours

**Tasks**:
- [ ] Create unit tests for environment variable resolution
- [ ] Test error handling for missing environment variables
- [ ] Test error handling for invalid format
- [ ] Test integration with existing parameter system
- [ ] Create integration tests with real ASDL files

**Test Files to Create**:
- `tests/unit_tests/elaborator/test_environment_variables.py`
- `tests/integration/test_environment_variables.py`

**Success Criteria**:
- [ ] All unit tests pass
- [ ] Error diagnostics generated correctly
- [ ] Integration tests demonstrate end-to-end functionality
- [ ] No regression in existing parameter resolution

## Error Codes

### E0501: Environment Variable Not Found
- **When**: Environment variable referenced in parameter value is not defined
- **Message**: "Environment variable ${VAR_NAME} not found in parameter 'param_name'"
- **Severity**: ERROR
- **Resolution**: Set the required environment variable or use a static value

### E0502: Invalid Environment Variable Format
- **When**: Parameter value contains malformed environment variable syntax
- **Message**: "Invalid environment variable format in parameter 'param_name': expected ${VAR} format"
- **Severity**: ERROR
- **Resolution**: Use correct `${VAR}` syntax in parameter value

## Example Usage

### Valid Syntax ✅
```yaml
parameters:
  pdk_root: ${PDK_ROOT}
  corner: ${CORNER}
  temp: ${TEMP}
  width: ${WIDTH}
```

### Invalid Syntax ❌
```yaml
parameters:
  pdk_root: $PDK_ROOT          # Missing braces
  corner: ${CORNER}/fast       # Contains path separator
  temp: ${TEMP:-25}            # Contains default value
  width: ${WIDTH}extra         # Contains extra text
```

## Integration Points

### VariableResolver
- **New Method**: `resolve_environment_variables(parameters: Dict) -> Dict`
- **Integration**: Called before `resolve_instance_variables()`
- **Output**: Parameters with environment variables resolved to concrete values

### Elaborator Pipeline
- **Phase**: Environment variable resolution during elaboration
- **Order**: Environment → Parameters → Instance Variables
- **Output**: All variables resolved before template substitution

### Generator
- **No Changes**: Uses existing `{param}` substitution mechanism
- **Input**: Parameters already resolved to concrete values
- **Output**: SPICE with environment-based values substituted

## Success Criteria

### Functional Requirements
- [ ] Environment variables resolved from `${VAR}` syntax
- [ ] Error diagnostics for missing environment variables
- [ ] Error diagnostics for invalid format
- [ ] Integration with existing parameter resolution
- [ ] No changes to generator or template logic

### Quality Requirements
- [ ] Comprehensive unit test coverage
- [ ] Integration tests with real ASDL files
- [ ] No regression in existing functionality
- [ ] Clear error messages with parameter context
- [ ] Clean separation of concerns

### Performance Requirements
- [ ] No significant performance impact on parameter resolution
- [ ] Environment variable resolution scales with parameter count
- [ ] No memory leaks from environment variable handling

## Future Enhancements (Not in Scope)

### Phase 2 Considerations
- [ ] Default value support: `${VAR:-default}`
- [ ] Nested environment variables: `${PDK_ROOT}/gf180mcu`
- [ ] Environment variable validation and security
- [ ] Configuration file support for environment variables
- [ ] CLI override of environment variables

### Documentation Updates
- [ ] Update parameter system documentation
- [ ] Add environment variable examples to user guide
- [ ] Update error code documentation
- [ ] Add troubleshooting guide for common issues

## Dependencies

### Required
- [ ] VariableResolver class exists and functional
- [ ] Diagnostic system supports new error codes
- [ ] Elaborator pipeline supports parameter resolution
- [ ] Test framework supports new test cases

### Optional
- [ ] Environment variable examples in test fixtures
- [ ] Integration test infrastructure
- [ ] Documentation generation tools

## Risk Assessment

### Low Risk
- **Implementation Complexity**: Simple string parsing and environment variable lookup
- **Integration Impact**: Minimal changes to existing pipeline
- **Testing Coverage**: Straightforward unit and integration testing

### Medium Risk
- **Error Handling**: Need to ensure comprehensive error coverage
- **Performance**: Environment variable resolution should not impact performance
- **User Experience**: Error messages should be clear and actionable

### Mitigation Strategies
- **Comprehensive Testing**: Unit tests for all code paths
- **Performance Monitoring**: Measure impact on parameter resolution
- **User Testing**: Validate error messages are clear and helpful
- **Incremental Implementation**: Phase-based approach with validation at each step
