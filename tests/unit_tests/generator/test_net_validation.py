"""
Test net declaration validation in SPICEGenerator.

Tests validation that all nets used in instance mappings are properly declared
as ports or internal nets, including pattern expansion handling.
"""

import pytest
import warnings
from src.asdl.generator import SPICEGenerator
from src.asdl.data_structures import (
    ASDLFile, FileInfo, Module, Instance, Port, PortDirection, 
    SignalType, DeviceModel, DeviceType, Nets
)


class TestNetDeclarationValidation:
    """Test validation of net declarations in modules."""

    def test_valid_net_declarations_no_warnings(self):
        """Test that properly declared nets generate no warnings."""
        # Create a module with all nets properly declared
        module = Module(
            doc="Test module with proper net declarations",
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            nets=Nets(internal=["internal_net"]),
            instances={
                "INST1": Instance(
                    model="test_device",
                    mappings={
                        "G": "in",          # Valid port
                        "D": "out",         # Valid port  
                        "S": "internal_net", # Valid internal net
                        "B": "vss"          # Valid port
                    }
                )
            }
        )
        
        # Create device model for the instance
        device_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            doc="Test device",
            device_line="MN {D} {G} {S} {B} nfet",
            parameters={"M": "1"}
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=FileInfo(
                top_module="test_module",
                doc="Test design",
                revision="1.0",
                author="test",
                date="2024-01-01"
            ),
            models={"test_device": device_model},
            modules={"test_module": module}
        )
        
        # Generate SPICE - should produce no warnings
        generator = SPICEGenerator()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            generator.generate(asdl_file)
            
            # Filter for net declaration warnings specifically
            net_warnings = [warning for warning in w 
                          if "undeclared nets" in str(warning.message)]
            assert len(net_warnings) == 0

    def test_undeclared_nets_warning(self):
        """Test that undeclared nets generate appropriate warnings."""
        # Create a module with undeclared nets used in mappings
        module = Module(
            doc="Test module with undeclared nets",
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            nets=Nets(internal=["valid_internal"]),
            instances={
                "INST1": Instance(
                    model="test_device",
                    mappings={
                        "G": "in",                    # Valid port
                        "D": "undeclared_out",        # UNDECLARED net
                        "S": "undeclared_source",     # UNDECLARED net  
                        "B": "vss"                    # Valid port
                    }
                )
            }
        )
        
        # Create device model for the instance
        device_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            doc="Test device",
            device_line="MN {D} {G} {S} {B} nfet",
            parameters={"M": "1"}
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=FileInfo(
                top_module="test_module",
                doc="Test design",
                revision="1.0",
                author="test", 
                date="2024-01-01"
            ),
            models={"test_device": device_model},
            modules={"test_module": module}
        )
        
        # Generate SPICE - should produce warnings for undeclared nets
        generator = SPICEGenerator()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            generator.generate(asdl_file)
            
            # Filter for net declaration warnings
            net_warnings = [warning for warning in w 
                          if "undeclared nets" in str(warning.message)]
            assert len(net_warnings) == 1
            
            warning_msg = str(net_warnings[0].message)
            assert "test_module" in warning_msg
            assert "undeclared_out" in warning_msg
            assert "undeclared_source" in warning_msg

    def test_pattern_expansion_validation(self):
        """Test net validation with pattern expansion."""
        # Create a module using pattern expansion
        module = Module(
            doc="Test module with pattern expansion",
            ports={
                "in_<p,n>": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            nets=Nets(internal=["tail"]),
            instances={
                "MN_<P,N>": Instance(
                    model="nmos_unit",
                    mappings={
                        "G": "in_<p,n>",         # Should expand to valid ports
                        "D": "out_<p,n>",        # Should expand to UNDECLARED nets
                        "S": "tail",             # Valid internal net
                        "B": "vss"               # Valid port
                    }
                )
            }
        )
        
        # Create device model
        device_model = DeviceModel(
            type=DeviceType.NMOS,
            ports=["G", "D", "S", "B"],
            doc="NMOS unit cell",
            device_line="MN {D} {G} {S} {B} nfet",
            parameters={"M": "1"}
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=FileInfo(
                top_module="test_module",
                doc="Test design",
                revision="1.0", 
                author="test",
                date="2024-01-01"
            ),
            models={"nmos_unit": device_model},
            modules={"test_module": module}
        )
        
        # Generate SPICE - should warn about expanded undeclared nets
        generator = SPICEGenerator()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            generator.generate(asdl_file)
            
            # Filter for net declaration warnings
            net_warnings = [warning for warning in w 
                          if "undeclared nets" in str(warning.message)]
            assert len(net_warnings) == 1
            
            warning_msg = str(net_warnings[0].message)
            assert "test_module" in warning_msg
            assert "out_p" in warning_msg  # Expanded from out_<p,n>
            assert "out_n" in warning_msg  # Expanded from out_<p,n>

    def test_real_world_ota_5t_issue(self):
        """Test the specific issue identified in two_stage_ota.yml ota_5t module."""
        # Recreate the problematic ota_5t module structure
        module = Module(
            doc="5-transistor OTA: differential pair with current mirror load",
            ports={
                "in_<p,n>": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE),
                "vbn": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "vss": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            nets=Nets(internal=["tail", "vd"]),  # Note: out_n and out_<p,n> are NOT declared
            instances={
                "MP_<P,N>": Instance(
                    model="pmos_unit",
                    mappings={
                        "G": "out_n",           # UNDECLARED - not in ports or internal nets
                        "D": "out_<p,n>",       # UNDECLARED - expands to out_p, out_n (not declared)
                        "S": "vdd",             # Valid port
                        "B": "vdd"              # Valid port
                    }
                )
            }
        )
        
        # Create device model
        device_model = DeviceModel(
            type=DeviceType.PMOS,
            ports=["G", "D", "S", "B"],
            doc="PMOS unit cell",
            device_line="MP {D} {G} {S} {B} pfet",
            parameters={"M": "1"}
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=FileInfo(
                top_module="ota_5t",
                doc="Test OTA design",
                revision="1.0",
                author="test",
                date="2024-01-01"
            ),
            models={"pmos_unit": device_model},
            modules={"ota_5t": module}
        )
        
        # Generate SPICE - should warn about the specific undeclared nets
        generator = SPICEGenerator()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            generator.generate(asdl_file)
            
            # Filter for net declaration warnings
            net_warnings = [warning for warning in w 
                          if "undeclared nets" in str(warning.message)]
            assert len(net_warnings) == 1
            
            warning_msg = str(net_warnings[0].message)
            assert "ota_5t" in warning_msg
            assert "out_n" in warning_msg    # From both G mapping and D pattern expansion
            assert "out_p" in warning_msg    # From D pattern expansion

    def test_no_instances_no_validation_error(self):
        """Test that modules with no instances don't cause validation errors."""
        # Create a module with no instances
        module = Module(
            doc="Empty module with no instances",
            ports={
                "in": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "out": Port(dir=PortDirection.OUT, type=SignalType.VOLTAGE)
            }
        )
        
        # Create ASDL file
        asdl_file = ASDLFile(
            file_info=FileInfo(
                top_module="empty_module",
                doc="Test design",
                revision="1.0",
                author="test",
                date="2024-01-01"
            ),
            models={},
            modules={"empty_module": module}
        )
        
        # Generate SPICE - should work without errors
        generator = SPICEGenerator()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = generator.generate(asdl_file)
            
            # Should not crash and should generate valid SPICE
            assert ".subckt empty_module in out" in result
            assert ".ends" in result
            
            # Should not generate net validation warnings
            net_warnings = [warning for warning in w 
                          if "undeclared nets" in str(warning.message)]
            assert len(net_warnings) == 0

    def test_mixed_valid_invalid_nets(self):
        """Test module with both valid and invalid net references."""
        module = Module(
            doc="Module with mixed valid/invalid nets",
            ports={
                "valid_port": Port(dir=PortDirection.IN, type=SignalType.VOLTAGE),
                "vdd": Port(dir=PortDirection.IN_OUT, type=SignalType.VOLTAGE)
            },
            nets=Nets(internal=["valid_internal"]),
            instances={
                "INST1": Instance(
                    model="test_device",
                    mappings={
                        "port1": "valid_port",      # Valid
                        "port2": "valid_internal",  # Valid
                        "port3": "invalid_net1",    # Invalid
                        "port4": "invalid_net2"     # Invalid  
                    }
                )
            }
        )
        
        device_model = DeviceModel(
            type=DeviceType.RESISTOR,
            ports=["port1", "port2", "port3", "port4"],
            doc="Multi-port test device",
            device_line="R {port1} {port2} R=1k",
            parameters={}
        )
        
        asdl_file = ASDLFile(
            file_info=FileInfo(
                top_module="mixed_module",
                doc="Test design",
                revision="1.0",
                author="test",
                date="2024-01-01"
            ),
            models={"test_device": device_model},
            modules={"mixed_module": module}
        )
        
        generator = SPICEGenerator()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            generator.generate(asdl_file)
            
            net_warnings = [warning for warning in w 
                          if "undeclared nets" in str(warning.message)]
            assert len(net_warnings) == 1
            
            warning_msg = str(net_warnings[0].message)
            assert "invalid_net1" in warning_msg
            assert "invalid_net2" in warning_msg
            # Should not mention valid nets
            assert "valid_port" not in warning_msg
            assert "valid_internal" not in warning_msg 