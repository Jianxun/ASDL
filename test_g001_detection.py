#!/usr/bin/env python3

"""Test G001 unresolved placeholder detection."""

import sys
sys.path.insert(0, 'src')

from asdl.generator import SPICEGenerator
from asdl.data_structures import (
    ASDLFile, Module, FileInfo, Instance
)

def test_g001_unresolved_placeholders():
    """Test that G001 error is generated for unresolved placeholders."""
    
    print("Testing G001 unresolved placeholder detection...")
    
    # Create a module with unresolved placeholders in spice_template
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="rc_filter"),
        modules={
            "rc_filter": Module(
                instances={
                    "R1": Instance(
                        model="resistor",
                        mappings={"1": "in", "2": "out"},
                    ),
                    "C1": Instance(
                        model="capacitor", 
                        mappings={"1": "out", "2": "gnd"},
                    )
                }
            ),
            "resistor": Module(
                spice_template="RR{name} {1} {2} {R_val} TC1=0 TC2=0"  # Missing R_val definition
            ),
            "capacitor": Module(
                spice_template="CC{name} {1} {2} {C_val}"  # Missing C_val definition
            )
        },
    )
    
    # Test generation
    generator = SPICEGenerator()
    spice_output, diagnostics = generator.generate(asdl_file)
    
    print(f"Generated SPICE:")
    print("=" * 50)
    print(spice_output)
    print("=" * 50)
    
    print(f"Diagnostics ({len(diagnostics)}):")
    for diag in diagnostics:
        print(f"  {diag.code}: {diag.title}")
        print(f"    {diag.details}")
    
    # Should detect unresolved placeholders
    assert len(diagnostics) == 1, f"Expected 1 diagnostic, got {len(diagnostics)}"
    assert diagnostics[0].code == "G001", f"Expected G001, got {diagnostics[0].code}"
    assert "R_val" in diagnostics[0].details, "Should mention R_val placeholder"
    assert "C_val" in diagnostics[0].details, "Should mention C_val placeholder"
    
    # Should still contain unresolved placeholders in output
    assert "{R_val}" in spice_output, "Should contain unresolved {R_val}"
    assert "{C_val}" in spice_output, "Should contain unresolved {C_val}"
    
    print("✅ G001 unresolved placeholder detection working correctly!")
    
    return True

if __name__ == "__main__":
    test_g001_unresolved_placeholders()