#!/usr/bin/env python3
"""
Replicate the exact failing test to understand what's different.
"""

import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from asdl.elaborator.import_.import_resolver import ImportResolver


def test_exact_replication():
    """Replicate the exact failing test."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create file A that imports B (EXACT copy from test)
        file_a_path = temp_path / "module_a.asdl"
        file_a_path.write_text("""
file_info:
  top_module: module_a
imports:
  module_b: module_b.asdl
modules:
  circuit_a:
    instances:
      B_INST: {model: module_b.circuit_b}
""")
        
        # Create file B that imports A (EXACT copy from test)
        file_b_path = temp_path / "module_b.asdl"
        file_b_path.write_text("""
file_info:
  top_module: module_b
imports:
  module_a: module_a.asdl
modules:
  circuit_b:
    instances:
      A_INST: {model: module_a.circuit_a}
""")
        
        print("=== EXACT TEST REPLICATION ===")
        print(f"Temp dir: {temp_path}")
        print(f"File A: {file_a_path}")
        print(f"File B: {file_b_path}")
        print()
        
        # Use same resolver setup as test
        resolver = ImportResolver()
        
        # Add debug logging
        original_load_recursive = resolver._load_file_recursive
        
        def debug_load_recursive(current_file, current_path, search_paths, loaded_files, all_diagnostics, loading_stack):
            print(f"🔄 _load_file_recursive:")
            print(f"   current_path: {current_path.name}")
            print(f"   loading_stack: {[p.name for p in loading_stack]}")
            print(f"   current_file.imports: {current_file.imports}")
            print(f"   loaded_files: {[p.name for p in loaded_files.keys()]}")
            print(f"   all_diagnostics before: {len(all_diagnostics)}")
            
            result = original_load_recursive(current_file, current_path, search_paths, loaded_files, all_diagnostics, loading_stack)
            
            print(f"   loaded_files after: {[p.name for p in loaded_files.keys()]}")
            print(f"   all_diagnostics after: {len(all_diagnostics)}")
            if all_diagnostics:
                for d in all_diagnostics[-3:]:  # Show last few
                    print(f"     - {d.code}: {d.title}")
            print()
            
            return result
        
        resolver._load_file_recursive = debug_load_recursive
        
        # Resolve imports (should detect circular dependency)
        result, diagnostics = resolver.resolve_imports(
            file_a_path,
            search_paths=[temp_path]
        )
        
        print("=== FINAL RESULTS ===")
        print(f"Result: {result is not None}")
        print(f"Diagnostics: {len(diagnostics)}")
        for d in diagnostics:
            print(f"  {d.code}: {d.title}")
            print(f"    {d.details}")
        print()
        
        # Check test expectations
        print("=== TEST ASSERTIONS ===")
        print(f"len(diagnostics) > 0: {len(diagnostics) > 0}")
        if len(diagnostics) > 0:
            circular_errors = [d for d in diagnostics if d.code == "E0442"]
            print(f"E0442 errors: {len(circular_errors)}")
            if circular_errors:
                has_circular_in_title = any("circular" in d.title.lower() for d in circular_errors)
                print(f"Has 'circular' in title: {has_circular_in_title}")
        else:
            print("❌ NO DIAGNOSTICS - This matches the failing test!")


if __name__ == "__main__":
    test_exact_replication()