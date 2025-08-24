#!/usr/bin/env python3
"""
Debug script to trace circular import detection step by step.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from asdl.elaborator.import_.import_resolver import ImportResolver


def debug_circular_imports():
    """Step through circular import detection with detailed logging."""
    
    examples_path = Path(__file__).parent.resolve()
    file_a_path = examples_path / 'module_a.asdl' 
    file_b_path = examples_path / 'module_b.asdl'
    
    print("=== DEBUGGING CIRCULAR IMPORT DETECTION ===")
    print(f"File A: {file_a_path}")
    print(f"File B: {file_b_path}")
    print(f"Search path: {examples_path}")
    print()
    
    # Patch import resolver to add logging
    resolver = ImportResolver()
    original_load_recursive = resolver._load_file_recursive
    
    def debug_load_recursive(current_file, current_path, search_paths, loaded_files, all_diagnostics, loading_stack):
        print(f"🔄 _load_file_recursive called:")
        print(f"   current_path: {current_path.name}")
        print(f"   loading_stack: {[p.name for p in loading_stack]}")
        print(f"   current_file.imports: {current_file.imports}")
        print()
        
        return original_load_recursive(current_file, current_path, search_paths, loaded_files, all_diagnostics, loading_stack)
    
    resolver._load_file_recursive = debug_load_recursive
    
    # Patch file loader to add logging  
    original_load_with_check = resolver.file_loader.load_file_with_dependency_check
    
    def debug_load_with_check(file_path, loading_stack=None):
        normalized_path = file_path.resolve()
        print(f"📁 load_file_with_dependency_check called:")
        print(f"   file_path: {normalized_path.name}")
        print(f"   loading_stack: {[p.name for p in (loading_stack or [])]}")
        print(f"   normalized_path in loading_stack: {normalized_path in (loading_stack or [])}")
        
        result = original_load_with_check(file_path, loading_stack)
        
        print(f"   result: file={result[0] is not None}, diagnostics={len(result[1])}")
        if result[1]:
            for d in result[1]:
                print(f"     - {d.code}: {d.title}")
        print()
        
        return result
    
    resolver.file_loader.load_file_with_dependency_check = debug_load_with_check
    
    # Run the test
    print("🚀 Starting import resolution...")
    result, diagnostics = resolver.resolve_imports(file_a_path, search_paths=[examples_path])
    
    print("=== FINAL RESULTS ===")
    print(f"Result: {result is not None}")
    print(f"Diagnostics: {len(diagnostics)}")
    for d in diagnostics:
        print(f"  {d.code}: {d.title}")
        print(f"    {d.details}")


if __name__ == "__main__":
    debug_circular_imports()