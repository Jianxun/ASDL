# ASDL Compiler Logging System Design

## Document Information
- **Date**: 2025-01-27
- **Status**: Design Document
- **Version**: 1.0
- **Scope**: Logging, debugging, and tracing capabilities for the ASDL compiler

## Executive Summary

The ASDL compiler currently has a basic logging system using `click.echo()` statements and a comprehensive diagnostic system. This document outlines the design for enhancing these capabilities with structured logging, advanced tracing, and debugging features to support development and troubleshooting.

## Current State Analysis

### Existing Infrastructure

#### 1. CLI-Level Logging (Basic)
- **Verbose Mode**: `-v/--verbose` flag available on all major commands
- **Stage Reporting**: Simple progress indicators using `click.echo()`
- **Output**: Human-readable progress messages for major pipeline stages
- **Limitations**: No structured format, limited information, console-only output

#### 2. Diagnostic System (Comprehensive)
- **XCCSS Error Codes**: Structured diagnostic system with location tracking
- **JSON Output**: Machine-readable diagnostic output with `--json` flag
- **Human Formatting**: User-friendly diagnostic display
- **Strengths**: Excellent error reporting, location tracking, structured output

#### 3. Current Limitations
- **No Structured Logging**: No Python `logging` module integration
- **No Log Levels**: Only binary verbose/non-verbose
- **No Trace IDs**: No correlation between related log entries
- **No File Logging**: All output goes to stdout/stderr
- **Limited Import Debugging**: No visibility into import resolution details
- **No Performance Metrics**: No timing or resource usage tracking

## Design Goals

### Primary Objectives
1. **Development Support**: Provide detailed debugging information for developers
2. **Troubleshooting**: Enable users to diagnose compilation issues
3. **Performance Analysis**: Track pipeline stage timing and resource usage
4. **Import Resolution Visibility**: Show detailed import resolution process
5. **Backward Compatibility**: Maintain existing CLI behavior

### Secondary Objectives
1. **Structured Output**: Machine-readable logs for automation
2. **Configurable Verbosity**: Multiple log levels for different use cases
3. **File Logging**: Persistent log storage for analysis
4. **Trace Correlation**: Unique identifiers for compilation runs

## Architecture Design

### 1. Logging Hierarchy

```
asdlc (root logger)
├── parser (parser logger)
├── elaborator (elaborator logger)
│   ├── imports (import resolver logger)
│   ├── patterns (pattern expansion logger)
│   └── variables (variable resolution logger)
├── validator (validator logger)
├── generator (generator logger)
└── cli (CLI interface logger)
```

### 2. Log Levels

| Level | CLI Flag | Use Case | Example Output |
|-------|----------|----------|----------------|
| ERROR | Always | Errors that prevent compilation | "Failed to parse file: syntax error" |
| WARNING | Always | Issues that don't stop compilation | "Deprecated syntax used" |
| INFO | `-v/--verbose` | General progress information | "Processing module 'inverter'" |
| DEBUG | `--debug` | Detailed debugging information | "Resolved import 'primitives' to /path/file.asdl" |
| TRACE | `--trace` | Extremely detailed execution flow | "Entering _load_file_recursive with stack depth 3" |

### 3. Log Format Structure

#### Human-Readable Format
```
[2025-01-27 14:30:15] [INFO] [parser] Parsing file: /path/to/file.asdl
[2025-01-27 14:30:15] [DEBUG] [imports] Search paths: ['/libs', '/custom']
[2025-01-27 14:30:16] [TRACE] [imports] Resolving import 'primitives' from /path/to/file.asdl
```

#### JSON Format (for automation)
```json
{
  "timestamp": "2025-01-27T14:30:15.123Z",
  "level": "INFO",
  "component": "parser",
  "message": "Parsing file: /path/to/file.asdl",
  "trace_id": "comp_20250127_143015_abc123",
  "metadata": {
    "file_path": "/path/to/file.asdl",
    "file_size": 1024
  }
}
```

## Implementation Plan

### Phase 1: Structured Logging Foundation

#### 1.1 Python Logging Integration
- **Replace `click.echo()`**: Convert existing verbose output to proper logging
- **Logger Configuration**: Set up hierarchical logger structure
- **Log Level Mapping**: Map CLI flags to appropriate log levels

#### 1.2 Log Formatting
- **Timestamp Format**: ISO 8601 with millisecond precision
- **Component Identification**: Clear component prefixes for all log entries
- **Message Formatting**: Consistent, readable message structure

#### 1.3 Output Configuration
- **Console Output**: Maintain existing human-readable output
- **File Output**: Optional log file with configurable path
- **JSON Output**: Structured format for automation tools

### Phase 2: Enhanced Tracing

#### 2.1 Trace ID System
- **Unique Identifiers**: Generate trace ID for each compilation run
- **Correlation**: Link all log entries from a single compilation
- **Format**: `comp_YYYYMMDD_HHMMSS_<hash>` for readability

#### 2.2 Import Resolution Tracing
- **Search Path Logging**: Show all search paths and resolution attempts
- **File Resolution**: Log successful and failed file lookups
- **Alias Mapping**: Track model alias resolution process
- **Circular Import Detection**: Detailed circular dependency logging

#### 2.3 Performance Metrics
- **Stage Timing**: Measure time for each pipeline stage
- **Memory Usage**: Track memory consumption during compilation
- **File I/O**: Monitor file read/write operations

### Phase 3: Advanced Debugging

#### 3.1 Configuration Dumping
- **Search Paths**: Show resolved search paths with source
- **Environment Variables**: Display resolved environment variables
- **File Dependencies**: List all imported files and their paths

#### 3.2 Step-by-Step Execution
- **Pipeline Stages**: Detailed breakdown of each compilation stage
- **Object State**: Optional detailed object state dumps
- **Decision Points**: Log key decision points in compilation

#### 3.3 Interactive Debug Mode
- **Pause Points**: Optional pauses at specific stages
- **State Inspection**: Dump object state for debugging
- **Step Execution**: Manual control over pipeline progression

## CLI Interface Design

### New Command Options

```bash
# Basic verbose logging (existing)
asdlc elaborate file.asdl -v

# Enhanced debugging
asdlc elaborate file.asdl --debug

# Detailed tracing
asdlc elaborate file.asdl --trace

# Log to file
asdlc elaborate file.asdl --log-file compile.log

# JSON log output
asdlc elaborate file.asdl --log-json

# Combined options
asdlc elaborate file.asdl --debug --log-file debug.log --log-json
```

### Log Level Mapping

| CLI Flag | Log Level | Description |
|----------|-----------|-------------|
| None | ERROR + WARNING | Default: errors and warnings only |
| `-v/--verbose` | INFO | Progress information |
| `--debug` | DEBUG | Detailed debugging information |
| `--trace` | TRACE | Extremely detailed execution flow |

## Configuration Management

### Environment Variables
```bash
# Global log level
export ASDL_LOG_LEVEL=DEBUG

# Log file path
export ASDL_LOG_FILE=/tmp/asdl.log

# Log format (human|json)
export ASDL_LOG_FORMAT=human

# Component-specific logging
export ASDL_LOG_IMPORTS=DEBUG
export ASDL_LOG_PARSER=INFO
```

### Configuration File
```yaml
# ~/.asdl/config.yaml
logging:
  level: INFO
  file: ~/.asdl/logs/compilation.log
  format: human
  components:
    imports: DEBUG
    parser: INFO
    validator: WARNING
```

## Performance Considerations

### 1. Logging Overhead
- **Conditional Logging**: Only execute logging code when level is enabled
- **Lazy Evaluation**: Avoid expensive string formatting for disabled log levels
- **Async Output**: Non-blocking log writing for file output

### 2. Memory Management
- **Log Rotation**: Automatic log file rotation to prevent disk space issues
- **Buffer Management**: Efficient buffering for high-volume logging
- **Cleanup**: Proper cleanup of log resources

### 3. File I/O Optimization
- **Buffered Writing**: Minimize disk I/O operations
- **Compression**: Optional log compression for long-running compilations
- **Streaming**: Stream logs to avoid memory accumulation

## Migration Strategy

### 1. Backward Compatibility
- **Existing Flags**: Maintain `-v/--verbose` behavior
- **Output Format**: Preserve existing human-readable output
- **Error Handling**: Keep existing error reporting behavior

### 2. Incremental Implementation
- **Phase 1**: Add structured logging without changing existing output
- **Phase 2**: Enhance tracing capabilities
- **Phase 3**: Add advanced debugging features

### 3. Testing Strategy
- **Unit Tests**: Test logging functionality in isolation
- **Integration Tests**: Verify logging works across pipeline stages
- **Performance Tests**: Ensure logging doesn't impact compilation speed

## Future Enhancements

### 1. Remote Logging
- **Network Output**: Send logs to remote logging services
- **Centralized Collection**: Aggregate logs from multiple compilations
- **Real-time Monitoring**: Live log streaming for CI/CD pipelines

### 2. Advanced Analytics
- **Performance Trends**: Track compilation performance over time
- **Error Patterns**: Identify common compilation issues
- **Usage Statistics**: Monitor feature usage and adoption

### 3. Integration Support
- **IDE Integration**: Log output in development environments
- **CI/CD Integration**: Structured logging for automated builds
- **Monitoring Tools**: Integration with observability platforms

## Conclusion

This logging system design provides a comprehensive foundation for debugging and tracing the ASDL compiler. The phased implementation approach ensures backward compatibility while gradually adding powerful new capabilities. The structured logging will significantly improve development productivity and troubleshooting capabilities while maintaining the excellent user experience of the current system.

## Appendix

### A. Log Level Definitions

- **ERROR**: Errors that prevent successful compilation
- **WARNING**: Issues that don't stop compilation but may cause problems
- **INFO**: General progress information and important state changes
- **DEBUG**: Detailed information useful for debugging
- **TRACE**: Extremely detailed execution flow information

### B. Component Loggers

- **parser**: File parsing and syntax analysis
- **elaborator**: Pattern expansion and parameter resolution
- **imports**: Import resolution and dependency management
- **validator**: Structural validation and rule checking
- **generator**: SPICE netlist generation
- **cli**: Command-line interface and user interaction

### C. Trace ID Format

```
comp_YYYYMMDD_HHMMSS_<hash>
  ^    ^         ^      ^
  |    |         |      |
  |    |         |      +-- 6-char hash for uniqueness
  |    |         +-- Time (HH:MM:SS)
  |    +-- Date (YYYY-MM-DD)
  +-- Compilation prefix
```

Example: `comp_20250127_143015_a1b2c3`
