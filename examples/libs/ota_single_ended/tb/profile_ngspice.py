#!/usr/bin/env python3
"""
Professional ngspice simulation profiler
Usage: python profile_ngspice.py [--runs N] [--spice-file FILE]
"""

import subprocess
import time
import statistics
import argparse
import sys
import os
from pathlib import Path

def run_ngspice_with_timing(spice_file):
    """Run ngspice and capture timing information"""
    start_time = time.perf_counter()
    
    try:
        # Run ngspice and capture output
        result = subprocess.run(
            ['ngspice', '-b', spice_file],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        # Check if simulation was successful
        if result.returncode != 0:
            print(f"Error running ngspice: {result.stderr}")
            return None
            
        return {
            'execution_time': execution_time,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print("Simulation timed out after 60 seconds")
        return None
    except FileNotFoundError:
        print("Error: ngspice not found. Please ensure it's installed and in PATH")
        return None

def get_memory_usage(spice_file):
    """Get memory usage using /usr/bin/time -l"""
    try:
        result = subprocess.run(
            ['/usr/bin/time', '-l', 'ngspice', '-b', spice_file],
            capture_output=True,
            text=True
        )
        
        # Parse memory information from stderr
        lines = result.stderr.split('\n')
        memory_info = {}
        
        for line in lines:
            if 'maximum resident set size' in line:
                memory_info['max_memory_bytes'] = int(line.strip().split()[0])
            elif 'page reclaims' in line:
                memory_info['page_reclaims'] = int(line.strip().split()[0])
            elif 'page faults' in line:
                memory_info['page_faults'] = int(line.strip().split()[0])
                
        return memory_info
        
    except Exception as e:
        print(f"Error getting memory usage: {e}")
        return {}

def profile_simulation(spice_file, runs=5):
    """Profile the ngspice simulation"""
    
    if not os.path.exists(spice_file):
        print(f"Error: SPICE file '{spice_file}' not found")
        return
        
    print(f"Profiling ngspice simulation: {spice_file}")
    print(f"Number of runs: {runs}")
    print("=" * 50)
    
    execution_times = []
    
    # Run multiple simulations
    for i in range(runs):
        print(f"Run {i+1}/{runs}...", end=' ')
        
        result = run_ngspice_with_timing(spice_file)
        if result is None:
            print("FAILED")
            continue
            
        execution_times.append(result['execution_time'])
        print(f"{result['execution_time']:.4f}s")
    
    if not execution_times:
        print("No successful runs to analyze")
        return
        
    # Get memory usage from one run
    print("\nGetting memory usage information...")
    memory_info = get_memory_usage(spice_file)
    
    # Calculate statistics
    print("\n" + "=" * 50)
    print("TIMING STATISTICS:")
    print(f"  Average time: {statistics.mean(execution_times):.4f}s")
    print(f"  Median time:  {statistics.median(execution_times):.4f}s")
    print(f"  Min time:     {min(execution_times):.4f}s")
    print(f"  Max time:     {max(execution_times):.4f}s")
    
    if len(execution_times) > 1:
        print(f"  Std deviation: {statistics.stdev(execution_times):.4f}s")
        print(f"  Variance:     {statistics.variance(execution_times):.6f}s²")
    
    # Memory statistics
    if memory_info:
        print("\nMEMORY STATISTICS:")
        if 'max_memory_bytes' in memory_info:
            mem_mb = memory_info['max_memory_bytes'] / (1024 * 1024)
            print(f"  Max memory:   {memory_info['max_memory_bytes']:,} bytes ({mem_mb:.2f} MB)")
        if 'page_reclaims' in memory_info:
            print(f"  Page reclaims: {memory_info['page_reclaims']:,}")
        if 'page_faults' in memory_info:
            print(f"  Page faults:   {memory_info['page_faults']:,}")
    
    # Performance analysis
    print("\nPERFORMANCE ANALYSIS:")
    avg_time = statistics.mean(execution_times)
    if avg_time < 0.1:
        print("  ✓ Very fast simulation (< 0.1s)")
    elif avg_time < 1.0:
        print("  ✓ Fast simulation (< 1s)")
    elif avg_time < 10.0:
        print("  • Moderate simulation time (< 10s)")
    else:
        print("  ⚠ Slow simulation (> 10s)")
        
    if len(execution_times) > 1:
        cv = statistics.stdev(execution_times) / statistics.mean(execution_times)
        if cv < 0.1:
            print("  ✓ Consistent timing (low variability)")
        else:
            print("  ⚠ Variable timing (high variability)")

def main():
    parser = argparse.ArgumentParser(description='Profile ngspice simulations')
    parser.add_argument('--runs', type=int, default=5, help='Number of runs (default: 5)')
    parser.add_argument('--spice-file', default='./tb_ota_5t.spice', help='SPICE file to profile')
    
    args = parser.parse_args()
    
    profile_simulation(args.spice_file, args.runs)

if __name__ == '__main__':
    main()
