#!/usr/bin/env python3
"""
Comprehensive NGSpice Profiling Comparison
Compares subprocess vs shared library profiling methods for ngspice simulations.

Usage: python compare_profiling_methods.py [--runs N] [--spice-file FILE]
"""

import subprocess
import time
import statistics
import argparse
import sys
import os
from pathlib import Path

def profile_subprocess_method(spice_file: str, runs: int = 5):
    """Profile using subprocess calls to ngspice"""
    print(f"=== SUBPROCESS METHOD ===")
    print(f"Running {runs} simulations using subprocess...")
    
    exec_times = []
    
    for i in range(runs):
        print(f"  Run {i+1}/{runs}: ", end='', flush=True)
        
        start_time = time.perf_counter()
        try:
            result = subprocess.run(
                ['ngspice', '-b', spice_file],
                capture_output=True,
                timeout=30,
                text=True
            )
            end_time = time.perf_counter()
            
            if result.returncode == 0:
                exec_time = end_time - start_time
                exec_times.append(exec_time)
                print(f"{exec_time:.4f}s")
            else:
                print("FAILED")
                print(f"    Error: {result.stderr[:100]}...")
                
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
        except Exception as e:
            print(f"ERROR: {e}")
    
    if exec_times:
        print(f"\n  Results:")
        print(f"    Average time: {statistics.mean(exec_times):.4f}s")
        print(f"    Median time:  {statistics.median(exec_times):.4f}s")
        print(f"    Min time:     {min(exec_times):.4f}s")
        print(f"    Max time:     {max(exec_times):.4f}s")
        if len(exec_times) > 1:
            print(f"    Std deviation: {statistics.stdev(exec_times):.4f}s")
        print(f"    Success rate: {len(exec_times)}/{runs} ({100*len(exec_times)/runs:.1f}%)")
    
    return exec_times

def profile_shared_library_method(spice_file: str, runs: int = 5):
    """Profile using shared library method"""
    print(f"\n=== SHARED LIBRARY METHOD ===")
    print(f"Running {runs} simulations using shared library...")
    
    try:
        # Import the shared library profiler
        from profile_ngspice_shared import NgspiceSharedProfiler
        
        profiler = NgspiceSharedProfiler()
        profiler.initialize()
        profiler.load_netlist(spice_file)
        
        results = []
        exec_times = []
        
        for i in range(runs):
            print(f"  Run {i+1}/{runs}: ", end='', flush=True)
            
            try:
                result = profiler.run_simulation()
                results.append(result)
                exec_times.append(result['execution_time'])
                
                print(f"{result['execution_time']:.4f}s")
                
            except Exception as e:
                print(f"ERROR: {e}")
        
        if exec_times:
            print(f"\n  Results:")
            print(f"    Average time: {statistics.mean(exec_times):.4f}s")
            print(f"    Median time:  {statistics.median(exec_times):.4f}s")
            print(f"    Min time:     {min(exec_times):.4f}s")
            print(f"    Max time:     {max(exec_times):.4f}s")
            if len(exec_times) > 1:
                print(f"    Std deviation: {statistics.stdev(exec_times):.4f}s")
            print(f"    Success rate: {len(exec_times)}/{runs} ({100*len(exec_times)/runs:.1f}%)")
            
            # Additional shared library specific metrics
            if results:
                avg_mem_delta = statistics.mean([r['memory_delta'] for r in results if r['success']]) / 1024 / 1024
                avg_peak_mem = statistics.mean([r['peak_traced_memory'] for r in results if r['success']]) / 1024 / 1024
                avg_messages = statistics.mean([r['message_count'] for r in results if r['success']])
                avg_data_points = statistics.mean([r['data_points'] for r in results if r['success']])
                
                print(f"    Memory delta avg: {avg_mem_delta:.2f} MB")
                print(f"    Peak memory avg:  {avg_peak_mem:.2f} MB")
                print(f"    Messages avg:     {avg_messages:.1f}")
                print(f"    Data points avg:  {avg_data_points:.1f}")
        
        return exec_times
        
    except ImportError as e:
        print(f"  Error: Cannot import shared library profiler: {e}")
        print(f"  Skipping shared library method.")
        return []
    except Exception as e:
        print(f"  Error: {e}")
        print(f"  Falling back to subprocess method for comparison.")
        return []

def compare_methods(subprocess_times, shared_lib_times):
    """Compare the two profiling methods"""
    print(f"\n=== COMPARISON ===")
    
    if not subprocess_times:
        print("No subprocess results to compare.")
        return
    
    if not shared_lib_times:
        print("No shared library results to compare.")
        return
    
    sub_avg = statistics.mean(subprocess_times)
    lib_avg = statistics.mean(shared_lib_times)
    
    print(f"Average Execution Times:")
    print(f"  Subprocess:      {sub_avg:.4f}s")
    print(f"  Shared Library:  {lib_avg:.4f}s")
    
    if lib_avg < sub_avg:
        speedup = sub_avg / lib_avg
        print(f"  Shared library is {speedup:.2f}x faster")
    else:
        slowdown = lib_avg / sub_avg  
        print(f"  Shared library is {slowdown:.2f}x slower")
    
    print(f"\nVariability (Standard Deviation):")
    if len(subprocess_times) > 1:
        sub_std = statistics.stdev(subprocess_times)
        print(f"  Subprocess:      {sub_std:.4f}s ({100*sub_std/sub_avg:.1f}%)")
    
    if len(shared_lib_times) > 1:
        lib_std = statistics.stdev(shared_lib_times)
        print(f"  Shared Library:  {lib_std:.4f}s ({100*lib_std/lib_avg:.1f}%)")
    
    print(f"\nOverhead Analysis:")
    # Estimate pure simulation time (minimum time observed)
    min_time = min(min(subprocess_times), min(shared_lib_times))
    sub_overhead = sub_avg - min_time
    lib_overhead = lib_avg - min_time
    
    print(f"  Estimated simulation time: {min_time:.4f}s")
    print(f"  Subprocess overhead:       {sub_overhead:.4f}s ({100*sub_overhead/sub_avg:.1f}%)")
    print(f"  Shared library overhead:   {lib_overhead:.4f}s ({100*lib_overhead/lib_avg:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='Compare ngspice profiling methods')
    parser.add_argument('--runs', type=int, default=5, help='Number of runs per method (default: 5)')
    parser.add_argument('--spice-file', default='./tb_ota_5t.spice', help='SPICE file to profile')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.spice_file):
        print(f"Error: SPICE file '{args.spice_file}' not found")
        sys.exit(1)
    
    print(f"Profiling NGSpice Simulation Methods")
    print(f"SPICE file: {args.spice_file}")
    print(f"Runs per method: {args.runs}")
    print("=" * 60)
    
    # Profile subprocess method
    subprocess_times = profile_subprocess_method(args.spice_file, args.runs)
    
    # Profile shared library method  
    shared_lib_times = profile_shared_library_method(args.spice_file, args.runs)
    
    # Compare results
    compare_methods(subprocess_times, shared_lib_times)
    
    # Recommendations
    print(f"\n=== RECOMMENDATIONS ===")
    if shared_lib_times and subprocess_times:
        lib_avg = statistics.mean(shared_lib_times)
        sub_avg = statistics.mean(subprocess_times)
        
        if lib_avg < sub_avg * 0.9:  # At least 10% faster
            print("✓ Use SHARED LIBRARY method for better performance")
            print("  - Lower latency per simulation")
            print("  - Better for batch processing")
            print("  - More detailed profiling capabilities")
        elif sub_avg < lib_avg * 0.9:  # Subprocess is significantly faster
            print("✓ Use SUBPROCESS method for better performance")
            print("  - Lower overhead for single simulations")
            print("  - Simpler setup")
        else:
            print("• Both methods have similar performance")
            print("  - Use subprocess for simplicity")
            print("  - Use shared library for advanced features")
    
    print("\nFor production use:")
    print("- Shared library: Better for applications with many simulations")
    print("- Subprocess: Better for one-off simulations and scripts")

if __name__ == '__main__':
    main()
