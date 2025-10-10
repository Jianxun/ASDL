# NGSpice Simulation Profiling Summary

This directory contains comprehensive profiling tools for NGSpice simulations, comparing different approaches and providing detailed performance analysis.

## Available Profiling Tools

### 1. Basic Time Command
```bash
time ngspice -b ./tb_ota_5t.spice
```
**Results:** ~0.057s total time
- Simple and quick
- Basic timing information only
- Good for quick checks

### 2. Detailed System Profiling  
```bash
/usr/bin/time -l ngspice -b ./tb_ota_5t.spice
```
**Results:** 
- Real: 0.08s, User: 0.05s, System: 0.01s
- Memory: ~15 MB peak
- Detailed system resource usage

### 3. Python Subprocess Profiler
```bash
python profile_ngspice.py --runs 5
```
**Results:**
- Average: 0.0569s
- Very fast for single simulations
- 15.7% timing variability
- Simple to use and understand

### 4. NGSpice Shared Library Profiler
```bash
python profile_ngspice_shared.py --runs 5
```
**Results:**
- Average: 0.1033s  
- More consistent timing (1.7% variability)
- Detailed memory profiling
- Callback-based data collection
- Better for batch processing

### 5. Comprehensive Comparison Tool
```bash
python compare_profiling_methods.py --runs 5
```
**Results:**
- Side-by-side comparison
- Performance analysis
- Overhead breakdown
- Usage recommendations

## Key Findings

### Performance Comparison
| Method | Average Time | Std Dev | Overhead | Best For |
|--------|-------------|---------|----------|----------|
| Subprocess | 0.0569s | 0.0090s (15.7%) | 10.8% | Single simulations |
| Shared Library | 0.1033s | 0.0017s (1.7%) | 50.9% | Batch processing |

### Recommendations

#### Use Subprocess Method When:
- Running individual simulations
- Simple scripting needs
- Quick performance checks
- Minimal setup required

#### Use Shared Library Method When:
- Running many simulations in batch
- Need detailed profiling data
- Building simulation applications
- Consistent timing is important
- Memory usage monitoring required

## Circuit Under Test

**File:** `tb_ota_5t.spice`
**Description:** 5-transistor OTA testbench with DC sweep
- **Analysis:** DC sweep from 0V to 1.8V, 0.01V steps (181 points)
- **Circuit:** NMOS differential pair, PMOS current mirror, NMOS tail
- **Technology:** GF180MCU PDK

## Simulation Characteristics

- **Data Points:** 181 (DC sweep)
- **Simulation Time:** ~50ms (pure simulation)
- **Memory Usage:** ~15 MB peak
- **Convergence:** Fast, no convergence issues

## Advanced Profiling Features

### Memory Profiling
The shared library profiler provides detailed memory analysis:
- Peak memory usage tracking
- Memory delta per simulation
- Python memory tracing with `tracemalloc`

### Message Monitoring
Captures NGSpice messages and status:
- Error messages
- Warning notifications
- Status updates
- Simulation progress

### Timing Breakdown
- Pure simulation time estimation
- Overhead analysis
- Variability assessment
- Statistical analysis

## Usage Examples

### Quick Performance Check
```bash
time ngspice -b ./tb_ota_5t.spice
```

### Detailed Analysis
```bash
python profile_ngspice.py --runs 10
```

### Method Comparison
```bash
python compare_profiling_methods.py --runs 10
```

### Custom SPICE File
```bash
python profile_ngspice_shared.py --spice-file my_circuit.spice --runs 5
```

## Files in This Directory

- `profile_ngspice.py` - Python subprocess-based profiler
- `profile_ngspice_shared.py` - NGSpice shared library profiler  
- `compare_profiling_methods.py` - Comprehensive comparison tool
- `simple_profile.sh` - Simple bash profiling script
- `PROFILING_SUMMARY.md` - This summary document
- `tb_ota_5t.spice` - Test circuit

## Technical Notes

### Shared Library Setup
The shared library profiler automatically detects NGSpice installations:
- Homebrew: `/opt/homebrew/Cellar/libngspice/*/lib/libngspice.*.dylib`
- System: `/usr/local/lib/libngspice.*`
- Fallback: Uses `ctypes.util.find_library()`

### Callback Functions
The shared library method uses callbacks for:
- Message handling (`sendChar`)
- Status updates (`sendStat`) 
- Data streaming (`sendData`)
- Initialization (`sendInitData`)
- Exit handling (`controlledExit`)

### Error Handling
Both methods include comprehensive error handling:
- Timeout protection
- Convergence failure detection
- Library loading failures
- Graceful fallback mechanisms

## Future Enhancements

1. **GPU Acceleration Profiling** - When NGSpice GPU support is available
2. **Parallel Simulation Profiling** - Multi-threading analysis
3. **Monte Carlo Profiling** - Statistical simulation analysis
4. **Interactive Profiling** - Real-time performance monitoring
5. **Cloud Profiling** - Distributed simulation performance

## Conclusion

For your current use case of profiling individual simulations, the **subprocess method** provides the best performance with minimal overhead. The shared library method offers more features and consistency, making it ideal for applications that run many simulations or need detailed profiling data.

Both methods successfully profile the OTA simulation, showing that the actual simulation time is very fast (~50ms) with most overhead coming from process startup and library initialization.
