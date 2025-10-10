#!/usr/bin/env python3

"""Test G0305 unresolved placeholder detection (XCCSS)."""

from src.asdl.generator import SPICEGenerator
from src.asdl.diagnostics import DiagnosticSeverity
from src.asdl.generator.options import GeneratorOptions
from src.asdl.data_structures import (
    ASDLFile, Module, FileInfo, Instance
)

def test_g001_unresolved_placeholders():
    """Test that G001 error is generated for unresolved placeholders."""
    
    print("Testing G0305 unresolved placeholder detection (XCCSS)...")
    
    # Create a module with unresolved placeholders in spice_template
    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="rc_filter"),
        modules={
            "rc_filter": Module(
                instances={
                    "R1": Instance(
                        model="resistor",
                        mappings={"n1": "in", "n2": "out"},
                    ),
                    "C1": Instance(
                        model="capacitor", 
                        mappings={"n1": "out", "n2": "gnd"},
                    )
                }
            ),
            "resistor": Module(
                spice_template="RR{name} {n1} {n2} {R_val} TC1=0 TC2=0"  # Missing R_val definition
            ),
            "capacitor": Module(
                spice_template="CC{name} {n1} {n2} {C_val}"  # Missing C_val definition
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
    assert diagnostics[0].code == "G0305", f"Expected G0305, got {diagnostics[0].code}"
    assert diagnostics[0].severity == DiagnosticSeverity.WARNING, "G0305 should be a WARNING"
    assert "R_val" in diagnostics[0].details, "Should mention R_val placeholder"
    assert "C_val" in diagnostics[0].details, "Should mention C_val placeholder"
    
    # Should still contain unresolved placeholders in output
    assert "{R_val}" in spice_output, "Should contain unresolved {R_val}"
    assert "{C_val}" in spice_output, "Should contain unresolved {C_val}"
    
    print("✅ G0305 unresolved placeholder detection working correctly!")


def test_g0602_jinja_placeholders_warning_and_template_mode_skip():
    """Double-brace placeholders emit G0602; template mode skips checks entirely."""

    asdl_file = ASDLFile(
        file_info=FileInfo(top_module="rc_filter"),
        modules={
            "rc_filter": Module(
                instances={
                    "R1": Instance(model="resistor", mappings={"n1": "in", "n2": "out"}),
                }
            ),
            "resistor": Module(
                spice_template="RR{name} {{n1}} {{n2}} {{R_val}}"
            ),
        },
    )

    # Normal mode: should warn with G0602 for Jinja placeholders
    gen = SPICEGenerator()
    _out, diags = gen.generate(asdl_file)
    codes = [d.code for d in diags]
    assert "G0602" in codes, f"Expected G0602 in {codes}"

    # Template mode: should skip placeholder checks
    gen_tmpl = SPICEGenerator(options=GeneratorOptions(template_mode=True))
    _out2, diags2 = gen_tmpl.generate(asdl_file)
    assert all(c not in ("G0305", "G0602") for c in [d.code for d in diags2])


