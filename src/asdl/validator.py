"""
ASDL validation functionality.

Provides validation services for ASDL designs before generation.
"""

from typing import List
from .data_structures import Instance, Module, ASDLFile
from .diagnostics import Diagnostic, DiagnosticSeverity


class ASDLValidator:
    """
    Validator for ASDL designs.
    
    Validates structural correctness and generates diagnostics for issues.
    """
    
    def validate_port_mappings(self, instance_id: str, instance: Instance, module: Module) -> List[Diagnostic]:
        """
        Validate that instance port mappings match the target module's port definition.
        
        Args:
            instance_id: Name of the instance for error reporting
            instance: Instance with mappings to validate
            module: Target module to validate against
            
        Returns:
            List of diagnostics (empty if valid)
        """
        diagnostics = []
        
        if not module.ports:
            # Module has no ports, but instance has mappings
            if instance.mappings:
                mapped_ports = list(instance.mappings.keys())
                diagnostic = Diagnostic(
                    code="V001",
                    title="Invalid Port Mapping",
                    details=f"Instance '{instance_id}' maps to ports {mapped_ports}, "
                           f"but module '{instance.model}' defines no ports",
                    severity=DiagnosticSeverity.ERROR
                )
                diagnostics.append(diagnostic)
            return diagnostics
        
        # Get valid port names from module definition
        valid_ports = set(module.ports.keys())
        mapped_ports = set(instance.mappings.keys()) if instance.mappings else set()
        
        # Check: All mapped ports must exist in module definition
        invalid_ports = mapped_ports - valid_ports
        if invalid_ports:
            diagnostic = Diagnostic(
                code="V002",
                title="Invalid Port Mapping",
                details=f"Instance '{instance_id}' maps to invalid ports: {sorted(invalid_ports)}. "
                       f"Module '{instance.model}' only defines ports: {sorted(valid_ports)}",
                severity=DiagnosticSeverity.ERROR
            )
            diagnostics.append(diagnostic)
        
        return diagnostics
    
    def validate_unused_components(self, asdl_file: ASDLFile) -> List[Diagnostic]:
        """
        Validate and identify unused models and modules.
        
        Args:
            asdl_file: Complete ASDL design to validate
            
        Returns:
            List of diagnostics (warnings for unused components)
        """
        diagnostics = []
        
        # Track what's used anywhere in the design
        used_models = set()
        used_modules = set()
        
        # Walk through every module to see what it instantiates
        for module_name, module in asdl_file.modules.items():
            if module.instances:
                for instance in module.instances.values():
                    if instance.model in asdl_file.models:
                        # This is a device instance
                        used_models.add(instance.model)
                    elif instance.model in asdl_file.modules:
                        # This is a module instance  
                        used_modules.add(instance.model)
        
        # Identify unused models
        defined_models = set(asdl_file.models.keys())
        unused_models = defined_models - used_models
        
        # Identify unused modules (exclude top module from unused warnings)
        defined_modules = set(asdl_file.modules.keys())
        unused_modules = defined_modules - used_modules
        
        # Remove top module from unused warnings since it's the entry point
        if asdl_file.file_info.top_module:
            unused_modules.discard(asdl_file.file_info.top_module)
        
        # Generate warning for unused models
        if unused_models:
            models_list = ", ".join(f"'{model}'" for model in sorted(unused_models))
            diagnostic = Diagnostic(
                code="V004",
                title="Unused Models",
                details=f"Unused models detected: {models_list}. "
                       f"These models are defined but never instantiated.",
                severity=DiagnosticSeverity.WARNING
            )
            diagnostics.append(diagnostic)
        
        # Generate warning for unused modules  
        if unused_modules:
            modules_list = ", ".join(f"'{module}'" for module in sorted(unused_modules))
            diagnostic = Diagnostic(
                code="V005",
                title="Unused Modules",
                details=f"Unused modules detected: {modules_list}. "
                       f"These modules are defined but never instantiated.",
                severity=DiagnosticSeverity.WARNING
            )
            diagnostics.append(diagnostic)
        
        return diagnostics
    
    def validate_net_declarations(self, module: Module, module_name: str) -> List[Diagnostic]:
        """
        Validate that all nets used in instance mappings are properly declared.
        
        Args:
            module: Module to validate
            module_name: Name of the module for error reporting
            
        Returns:
            List of diagnostics (warnings for undeclared nets)
        """
        diagnostics = []
        
        if not module.instances:
            return diagnostics
        
        # Get all declared nets (ports + internal nets)
        declared_nets = set()
        
        # Add all declared ports
        if module.ports:
            declared_nets.update(module.ports.keys())
        
        # Add internal nets if declared
        if module.internal_nets:
            declared_nets.update(module.internal_nets)
        
        # Check all nets used in instance mappings
        undeclared_nets = set()
        for instance_id, instance in module.instances.items():
            if not instance.mappings:
                continue
                
            for port_name, net_name in instance.mappings.items():
                # Single net name (simplified for now - no pattern expansion)
                if net_name not in declared_nets:
                    undeclared_nets.add(net_name)
        
        # Generate warning for undeclared nets
        if undeclared_nets:
            nets_list = ", ".join(f"'{net}'" for net in sorted(undeclared_nets))
            diagnostic = Diagnostic(
                code="V003",
                title="Undeclared Nets",
                details=f"In module '{module_name}', undeclared nets used in instance mappings: {nets_list}. "
                       f"These nets are not declared as ports or internal nets.",
                severity=DiagnosticSeverity.WARNING
            )
            diagnostics.append(diagnostic)
        
        return diagnostics 