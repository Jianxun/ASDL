#!/usr/bin/env python3
"""
NGSpice Shared Library Profiler
Profiles simulation time using the ngspice shared library (libngspice) instead of subprocess calls.
This provides more detailed profiling capabilities and better integration.

Usage: python profile_ngspice_shared.py [--runs N] [--spice-file FILE]
"""

import ctypes
import ctypes.util
import time
import statistics
import argparse
import sys
import os
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any
import psutil
import tracemalloc

# Callback function types for ngspice
SendCharType = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
SendStatType = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
ControlledExitType = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
SendDataType = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
SendInitDataType = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int, ctypes.c_void_p)
BGThreadRunningType = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)

class NgspiceSharedProfiler:
    """Profiler for ngspice shared library simulations"""
    
    def __init__(self):
        self.ngspice = None
        self.messages = []
        self.simulation_data = []
        self.timing_data = {}
        self._load_library()
        self._setup_callbacks()
    
    def _load_library(self):
        """Load the ngspice shared library"""
        # Try to find libngspice
        lib_path = None
        
        # Common library names and paths
        lib_names = ['ngspice', 'libngspice.so', 'libngspice.dylib', 'libngspice.0.dylib', 'libngspice.dll']
        search_paths = [
            '/usr/local/lib',
            '/usr/lib', 
            '/opt/homebrew/lib',  # macOS Homebrew
            '/opt/homebrew/Cellar/libngspice/45.2/lib',  # Specific homebrew version
            '/usr/lib/x86_64-linux-gnu',  # Ubuntu/Debian
        ]
        
        # Try explicit paths first (more reliable than find_library)
        for search_path in search_paths:
            for name in lib_names:
                full_path = os.path.join(search_path, name)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    lib_path = full_path
                    break
            if lib_path:
                break
        
        # Fallback to ctypes.util.find_library
        if not lib_path:
            for name in lib_names:
                lib_path = ctypes.util.find_library(name)
                if lib_path:
                    break
        
        if not lib_path:
            raise RuntimeError(
                "Could not find ngspice shared library. Please install ngspice with shared library support.\n"
                "On macOS: brew install ngspice --with-ngshared\n"
                "On Ubuntu: apt-get install libngspice0-dev\n"
                "Or compile ngspice with --enable-xspice --enable-cider --enable-shared"
            )
        
        try:
            self.ngspice = ctypes.CDLL(lib_path)
        except OSError as e:
            raise RuntimeError(f"Failed to load ngspice library from {lib_path}: {e}")
        
        # Define function prototypes
        self._define_function_prototypes()
        
        print(f"Successfully loaded ngspice shared library from: {lib_path}")
    
    def _define_function_prototypes(self):
        """Define ctypes function prototypes for ngspice functions"""
        
        # ngSpice_Init
        self.ngspice.ngSpice_Init.argtypes = [
            SendCharType, SendStatType, ControlledExitType, 
            SendDataType, SendInitDataType, BGThreadRunningType, 
            ctypes.c_void_p
        ]
        self.ngspice.ngSpice_Init.restype = ctypes.c_int
        
        # ngSpice_Command
        self.ngspice.ngSpice_Command.argtypes = [ctypes.c_char_p]
        self.ngspice.ngSpice_Command.restype = ctypes.c_int
        
        # ngSpice_Circ
        self.ngspice.ngSpice_Circ.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
        self.ngspice.ngSpice_Circ.restype = ctypes.c_int
        
        # ngGet_Vec_Info (optional, for getting vector information)
        try:
            self.ngspice.ngGet_Vec_Info.argtypes = [ctypes.c_char_p]
            self.ngspice.ngGet_Vec_Info.restype = ctypes.c_void_p
        except AttributeError:
            pass  # Some versions don't have this function
    
    def _setup_callbacks(self):
        """Setup callback functions for ngspice"""
        
        @SendCharType
        def send_char_callback(message, msg_id, user_data):
            """Callback for ngspice messages"""
            try:
                msg = message.decode('utf-8', errors='ignore')
                self.messages.append({
                    'timestamp': time.time(),
                    'message': msg.strip(),
                    'id': msg_id
                })
                # Print important messages
                if msg_id in [1, 2, 3]:  # Error, warning, info
                    print(f"NGSpice: {msg.strip()}")
            except Exception as e:
                print(f"Error in send_char_callback: {e}")
            return 0
        
        @SendStatType  
        def send_stat_callback(status, msg_id, user_data):
            """Callback for ngspice status messages"""
            try:
                stat = status.decode('utf-8', errors='ignore')
                print(f"NGSpice Status: {stat.strip()}")
            except Exception:
                pass
            return 0
        
        @ControlledExitType
        def controlled_exit_callback(exit_status, immediate, quit_requested, exit_code, user_data):
            """Callback for ngspice controlled exit"""
            print(f"NGSpice exit: status={exit_status}, code={exit_code}")
            return exit_status
        
        @SendDataType
        def send_data_callback(data, num_vars, point_count, user_data):
            """Callback for simulation data"""
            try:
                # Store data point information
                self.simulation_data.append({
                    'timestamp': time.time(),
                    'point_count': point_count,
                    'num_vars': num_vars
                })
            except Exception as e:
                print(f"Error in send_data_callback: {e}")
            return 0
        
        @SendInitDataType
        def send_init_data_callback(vec_info, num_vecs, user_data):
            """Callback for simulation initialization data"""
            try:
                print(f"NGSpice: Initialized {num_vecs} vectors")
            except Exception as e:
                print(f"Error in send_init_data_callback: {e}")
            return 0
        
        @BGThreadRunningType
        def bg_thread_running_callback(is_running, msg_id, user_data):
            """Callback for background thread status"""
            return 0
        
        # Store callbacks as instance variables to prevent garbage collection
        self.send_char_cb = send_char_callback
        self.send_stat_cb = send_stat_callback
        self.controlled_exit_cb = controlled_exit_callback
        self.send_data_cb = send_data_callback
        self.send_init_data_cb = send_init_data_callback
        self.bg_thread_cb = bg_thread_running_callback
    
    def initialize(self):
        """Initialize the ngspice shared library"""
        result = self.ngspice.ngSpice_Init(
            self.send_char_cb,
            self.send_stat_cb, 
            self.controlled_exit_cb,
            self.send_data_cb,
            self.send_init_data_cb,
            self.bg_thread_cb,
            None
        )
        
        if result != 0:
            raise RuntimeError(f"Failed to initialize ngspice: return code {result}")
        
        print("NGSpice shared library initialized successfully")
    
    def load_netlist(self, spice_file: str):
        """Load a SPICE netlist into ngspice"""
        if not os.path.exists(spice_file):
            raise FileNotFoundError(f"SPICE file not found: {spice_file}")
        
        # Read the netlist file
        with open(spice_file, 'r') as f:
            lines = f.readlines()
        
        # Convert to array of C strings
        c_lines = []
        for line in lines:
            c_lines.append(ctypes.c_char_p(line.encode('utf-8')))
        
        # Add null terminator
        c_lines.append(ctypes.c_char_p(None))
        
        # Convert to ctypes array
        lines_array = (ctypes.c_char_p * len(c_lines))(*c_lines)
        
        # Load the circuit
        result = self.ngspice.ngSpice_Circ(lines_array)
        if result != 0:
            raise RuntimeError(f"Failed to load netlist: return code {result}")
        
        print(f"Loaded netlist: {spice_file}")
    
    def run_simulation(self) -> Dict[str, Any]:
        """Run the simulation and return timing information"""
        
        # Clear previous data
        self.messages.clear()
        self.simulation_data.clear()
        
        # Start memory and time profiling
        tracemalloc.start()
        process = psutil.Process()
        start_memory = process.memory_info().rss
        start_time = time.perf_counter()
        start_cpu = process.cpu_percent()
        
        try:
            # Run the simulation (the .control section should handle this)
            result = self.ngspice.ngSpice_Command(b"run")
            
            if result != 0:
                print(f"Warning: ngSpice_Command returned {result}")
            
            # Wait a bit for callbacks to complete
            time.sleep(0.1)
            
        finally:
            # Stop profiling
            end_time = time.perf_counter()
            end_memory = process.memory_info().rss
            end_cpu = process.cpu_percent()
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        
        # Calculate metrics
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        return {
            'execution_time': execution_time,
            'start_memory': start_memory,
            'end_memory': end_memory,
            'memory_delta': memory_delta,
            'peak_traced_memory': peak,
            'current_traced_memory': current,
            'cpu_percent': end_cpu,
            'message_count': len(self.messages),
            'data_points': len(self.simulation_data),
            'success': result == 0
        }

def profile_with_shared_library(spice_file: str, runs: int = 5) -> None:
    """Profile simulation using ngspice shared library"""
    
    print(f"Profiling with NGSpice Shared Library")
    print(f"SPICE file: {spice_file}")
    print(f"Number of runs: {runs}")
    print("=" * 60)
    
    try:
        profiler = NgspiceSharedProfiler()
        profiler.initialize()
        
        # Load the netlist once
        profiler.load_netlist(spice_file)
        
        results = []
        
        # Run multiple simulations
        for i in range(runs):
            print(f"\nRun {i+1}/{runs}:")
            
            try:
                result = profiler.run_simulation()
                results.append(result)
                
                print(f"  Execution time: {result['execution_time']:.4f}s")
                print(f"  Memory delta: {result['memory_delta']/1024/1024:.2f} MB")
                print(f"  Peak memory: {result['peak_traced_memory']/1024/1024:.2f} MB")
                print(f"  Data points: {result['data_points']}")
                print(f"  Messages: {result['message_count']}")
                
            except Exception as e:
                print(f"  Error in run {i+1}: {e}")
                continue
        
        # Calculate statistics
        if results:
            print("\n" + "=" * 60)
            print("STATISTICS:")
            
            exec_times = [r['execution_time'] for r in results if r['success']]
            memory_deltas = [r['memory_delta'] for r in results if r['success']]
            peak_memories = [r['peak_traced_memory'] for r in results if r['success']]
            
            if exec_times:
                print(f"Execution Time:")
                print(f"  Average: {statistics.mean(exec_times):.4f}s")
                print(f"  Median:  {statistics.median(exec_times):.4f}s")
                print(f"  Min:     {min(exec_times):.4f}s")
                print(f"  Max:     {max(exec_times):.4f}s")
                if len(exec_times) > 1:
                    print(f"  Std Dev: {statistics.stdev(exec_times):.4f}s")
            
            if memory_deltas:
                print(f"\nMemory Usage:")
                avg_mem = statistics.mean(memory_deltas) / 1024 / 1024
                print(f"  Average delta: {avg_mem:.2f} MB")
                
            if peak_memories:
                avg_peak = statistics.mean(peak_memories) / 1024 / 1024
                print(f"  Average peak: {avg_peak:.2f} MB")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nFalling back to subprocess-based profiling...")
        
        # Fallback to subprocess method
        fallback_profile_subprocess(spice_file, runs)

def fallback_profile_subprocess(spice_file: str, runs: int):
    """Fallback profiling using subprocess calls"""
    import subprocess
    
    print(f"\nFallback: Using subprocess method")
    print("=" * 40)
    
    exec_times = []
    
    for i in range(runs):
        print(f"Run {i+1}/{runs}: ", end='')
        
        start_time = time.perf_counter()
        try:
            result = subprocess.run(
                ['ngspice', '-b', spice_file],
                capture_output=True,
                timeout=30
            )
            end_time = time.perf_counter()
            
            if result.returncode == 0:
                exec_time = end_time - start_time
                exec_times.append(exec_time)
                print(f"{exec_time:.4f}s")
            else:
                print("FAILED")
                
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
        except Exception as e:
            print(f"ERROR: {e}")
    
    if exec_times:
        print(f"\nSubprocess Statistics:")
        print(f"  Average: {statistics.mean(exec_times):.4f}s")
        print(f"  Min:     {min(exec_times):.4f}s")
        print(f"  Max:     {max(exec_times):.4f}s")

def main():
    parser = argparse.ArgumentParser(description='Profile ngspice simulations using shared library')
    parser.add_argument('--runs', type=int, default=5, help='Number of runs (default: 5)')
    parser.add_argument('--spice-file', default='./tb_ota_5t.spice', help='SPICE file to profile')
    
    args = parser.parse_args()
    
    profile_with_shared_library(args.spice_file, args.runs)

if __name__ == '__main__':
    main()
