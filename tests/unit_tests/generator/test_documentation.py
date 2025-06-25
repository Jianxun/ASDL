"""
Test suite for documentation features in SPICE generation.

Tests the conversion of instance `doc` fields to SPICE comments.
"""

import pytest
from src.asdl.data_structures import (
    ASDLFile, FileInfo, DeviceModel, Module, Instance, Port,
    DeviceType, PortDirection, SignalType
)
from src.asdl.generator import SPICEGenerator


class TestInstanceDocumentation:
    """Test instance documentation conversion to SPICE comments."""
    
    def test_instance_doc_as_spice_comment(self):
        """Test that instance doc field generates SPICE comment."""
        # Create test components
        file_info = FileInfo(
            top_module="test_circuit",
            doc="Test circuit for documentation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        # Simple device model
        nmos_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_model",
            parameters={"W": "1u", "L": "0.1u"}
        )
        
        # Module with documented instance
        test_module = Module(
            doc="Test module with documented instances",
            ports={
                "in": Port(PortDirection.IN, SignalType.VOLTAGE),
                "out": Port(PortDirection.OUT, SignalType.VOLTAGE)
            },
            instances={
                "MN1": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"},
                    doc="Input NMOS transistor with high gain",  # Documentation
                    parameters={"M": "2"}
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"nmos_unit": nmos_model},
            modules={"test_circuit": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify instance documentation appears as comment
        assert "* Input NMOS transistor with high gain" in spice_output
        assert "X_MN1 in out vss vss nmos_unit M=2" in spice_output
        
        # Verify comment appears before the instance line
        lines = spice_output.split('\n')
        comment_line_idx = None
        instance_line_idx = None
        
        for i, line in enumerate(lines):
            if "* Input NMOS transistor with high gain" in line:
                comment_line_idx = i
            if "X_MN1 in out vss vss nmos_unit M=2" in line:
                instance_line_idx = i
        
        assert comment_line_idx is not None, "Instance documentation comment not found"
        assert instance_line_idx is not None, "Instance line not found"
        assert comment_line_idx == instance_line_idx - 1, "Comment should appear immediately before instance"
    
    def test_multiple_instances_with_docs(self):
        """Test multiple instances with different documentation."""
        file_info = FileInfo(
            top_module="multi_doc_test",
            doc="Test multiple instance documentation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        # Device models
        nmos_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_model"
        )
        
        pmos_model = DeviceModel(
            type=DeviceType.PMOS,
            ports=["G", "D", "S", "B"],
            device_line="MP {D} {G} {S} {B} pfet_model"
        )
        
        # Module with multiple documented instances
        test_module = Module(
            doc="Test module with multiple documented instances",
            ports={
                "in": Port(PortDirection.IN, SignalType.VOLTAGE),
                "out": Port(PortDirection.OUT, SignalType.VOLTAGE)
            },
            instances={
                "MN_INPUT": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"},
                    doc="Input NMOS transistor for amplification",
                    parameters={"M": "1"}
                ),
                "MP_LOAD": Instance(
                    model="pmos_unit", 
                    mappings={"G": "bias", "D": "out", "S": "vdd", "B": "vdd"},
                    doc="PMOS load transistor for current source",
                    parameters={"M": "2"}
                ),
                "MN_CASC": Instance(
                    model="nmos_unit",
                    mappings={"G": "casc_bias", "D": "out", "S": "int", "B": "vss"},
                    doc="Cascode NMOS for higher output impedance"
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"nmos_unit": nmos_model, "pmos_unit": pmos_model},
            modules={"multi_doc_test": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify all instance documentation appears
        assert "* Input NMOS transistor for amplification" in spice_output
        assert "* PMOS load transistor for current source" in spice_output
        assert "* Cascode NMOS for higher output impedance" in spice_output
        
        # Verify corresponding instance lines exist
        assert "X_MN_INPUT" in spice_output
        assert "X_MP_LOAD" in spice_output  
        assert "X_MN_CASC" in spice_output
    
    def test_instance_without_doc_no_comment(self):
        """Test that instances without doc field don't generate comments."""
        file_info = FileInfo(
            top_module="no_doc_test",
            doc="Test instances without documentation",
            revision="1.0",
            author="test", 
            date="2024-01-01"
        )
        
        nmos_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_model"
        )
        
        # Module with instance that has NO documentation
        test_module = Module(
            doc="Test module",
            ports={
                "in": Port(PortDirection.IN, SignalType.VOLTAGE),
                "out": Port(PortDirection.OUT, SignalType.VOLTAGE)
            },
            instances={
                "MN1": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"},
                    # No doc field
                    parameters={"M": "1"}
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"nmos_unit": nmos_model},
            modules={"no_doc_test": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify instance line exists but no extra comment
        assert "X_MN1 in out vss vss nmos_unit M=1" in spice_output
        
        # Check that there's no instance-specific comment before the instance line
        lines = spice_output.split('\n')
        for i, line in enumerate(lines):
            if "X_MN1" in line and i > 0:
                # Check that the previous line is not an instance comment
                prev_line = lines[i-1].strip()
                # It could be a module comment, parameter, or other structural element
                # But it shouldn't be a specific instance comment like "* Some instance description"
                if prev_line.startswith('*') and not prev_line.startswith('* Test module'):
                    # This would be an unexpected instance comment
                    assert False, f"Unexpected instance comment found: {prev_line}"
    
    def test_mixed_documented_and_undocumented_instances(self):
        """Test module with mix of documented and undocumented instances."""
        file_info = FileInfo(
            top_module="mixed_doc_test",
            doc="Test mixed documentation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        nmos_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_model"
        )
        
        # Module with mix of documented and undocumented instances
        test_module = Module(
            doc="Mixed documentation test module",
            ports={
                "in": Port(PortDirection.IN, SignalType.VOLTAGE),
                "out": Port(PortDirection.OUT, SignalType.VOLTAGE)
            },
            instances={
                "MN_DOCUMENTED": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"},
                    doc="This instance has documentation",
                    parameters={"M": "1"}
                ),
                "MN_UNDOCUMENTED": Instance(
                    model="nmos_unit",
                    mappings={"G": "bias", "D": "out2", "S": "vss", "B": "vss"},
                    # No doc field
                    parameters={"M": "2"}
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"nmos_unit": nmos_model},
            modules={"mixed_doc_test": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify documented instance has comment
        assert "* This instance has documentation" in spice_output
        assert "X_MN_DOCUMENTED" in spice_output
        
        # Verify undocumented instance exists but has no specific comment
        assert "X_MN_UNDOCUMENTED" in spice_output
        
        # More specific check: the documented instance should have a comment before it
        lines = spice_output.split('\n')
        doc_comment_found = False
        doc_instance_found = False
        undoc_comment_found = False
        
        for i, line in enumerate(lines):
            if "* This instance has documentation" in line:
                doc_comment_found = True
                # Next non-empty line should be the instance
                if i + 1 < len(lines) and "X_MN_DOCUMENTED" in lines[i + 1]:
                    doc_instance_found = True
            
            if "X_MN_UNDOCUMENTED" in line and i > 0:
                # Check that previous line is not an instance-specific comment
                prev_line = lines[i-1].strip()
                if prev_line.startswith('*') and 'undocumented' in prev_line.lower():
                    undoc_comment_found = True
        
        assert doc_comment_found, "Documented instance comment not found"
        assert doc_instance_found, "Documented instance not found after comment"
        assert not undoc_comment_found, "Undocumented instance should not have instance-specific comment"

    def test_hierarchical_instances_with_docs(self):
        """Test documentation in hierarchical module instances."""
        file_info = FileInfo(
            top_module="hierarchical_test",
            doc="Test hierarchical instance documentation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        # Device model
        nmos_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_model"
        )
        
        # Sub-module
        amp_module = Module(
            doc="Amplifier submodule",
            ports={
                "in": Port(PortDirection.IN, SignalType.VOLTAGE),
                "out": Port(PortDirection.OUT, SignalType.VOLTAGE)
            },
            instances={
                "MN1": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"},
                    doc="Amplifier input transistor"
                )
            }
        )
        
        # Top-level module
        top_module = Module(
            doc="Top-level test module",
            ports={
                "signal_in": Port(PortDirection.IN, SignalType.VOLTAGE),
                "signal_out": Port(PortDirection.OUT, SignalType.VOLTAGE)
            },
            instances={
                "AMP1": Instance(
                    model="amplifier",
                    mappings={"in": "signal_in", "out": "signal_out"},
                    doc="First stage amplifier for signal processing"
                ),
                "AMP2": Instance(
                    model="amplifier", 
                    mappings={"in": "signal_out", "out": "final_out"},
                    doc="Second stage amplifier for output drive"
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"nmos_unit": nmos_model},
            modules={"amplifier": amp_module, "hierarchical_test": top_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify all documentation appears correctly
        assert "* Amplifier input transistor" in spice_output
        assert "* First stage amplifier for signal processing" in spice_output
        assert "* Second stage amplifier for output drive" in spice_output
        
        # Verify instance calls
        assert "X_MN1" in spice_output
        assert "X_AMP1" in spice_output
        assert "X_AMP2" in spice_output

    def test_doc_field_with_special_characters(self):
        """Test instance documentation with special characters and formatting."""
        file_info = FileInfo(
            top_module="special_chars_test",
            doc="Test special characters in documentation",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        nmos_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_model"
        )
        
        # Instance with special characters in documentation
        test_module = Module(
            doc="Test module",
            ports={
                "in": Port(PortDirection.IN, SignalType.VOLTAGE),
                "out": Port(PortDirection.OUT, SignalType.VOLTAGE)
            },
            instances={
                "MN_SPECIAL": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"},
                    doc="NMOS with W/L=10μm/0.18μm, gm/Id≈8, fo≈1GHz @ Vdd=1.8V",
                    parameters={"M": "1"}
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"nmos_unit": nmos_model},
            modules={"special_chars_test": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Verify special characters are preserved in comments
        assert "* NMOS with W/L=10μm/0.18μm, gm/Id≈8, fo≈1GHz @ Vdd=1.8V" in spice_output
        assert "X_MN_SPECIAL" in spice_output

    def test_empty_doc_field(self):
        """Test instance with empty doc field."""
        file_info = FileInfo(
            top_module="empty_doc_test",
            doc="Test empty documentation field",
            revision="1.0",
            author="test",
            date="2024-01-01"
        )
        
        nmos_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            device_line="MN {D} {G} {S} {B} nfet_model"
        )
        
        # Instance with empty doc field
        test_module = Module(
            doc="Test module",
            ports={
                "in": Port(PortDirection.IN, SignalType.VOLTAGE),
                "out": Port(PortDirection.OUT, SignalType.VOLTAGE)
            },
            instances={
                "MN1": Instance(
                    model="nmos_unit",
                    mappings={"G": "in", "D": "out", "S": "vss", "B": "vss"},
                    doc="",  # Empty documentation
                    parameters={"M": "1"}
                )
            }
        )
        
        asdl_file = ASDLFile(
            file_info=file_info,
            models={"nmos_unit": nmos_model},
            modules={"empty_doc_test": test_module}
        )
        
        # Generate SPICE
        generator = SPICEGenerator()
        spice_output = generator.generate(asdl_file)
        
        # Empty doc should not generate a comment
        assert "X_MN1" in spice_output
        
        # Check that no empty comment line appears before the instance
        lines = spice_output.split('\n')
        for i, line in enumerate(lines):
            if "X_MN1" in line and i > 0:
                prev_line = lines[i-1].strip()
                # Previous line should not be just "  *" (empty comment)
                assert prev_line != "*", "Empty doc field should not generate empty comment"
                assert prev_line != "  *", "Empty doc field should not generate empty comment" 