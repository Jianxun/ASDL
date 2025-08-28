"""
ASDL validation functionality.

Provides validation services for ASDL designs before generation.
"""

from typing import List
from .data_structures import Instance, Module, ASDLFile
from .diagnostics import Diagnostic, DiagnosticSeverity
from .validator_diagnostics import create_validator_diagnostic


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
                diagnostic = create_validator_diagnostic(
                    "V0301",
                    instance_id=instance_id,
                    mapped_ports=mapped_ports,
                    module_name=instance.model,
                )
                diagnostics.append(diagnostic)
            return diagnostics
        
        # Get valid port names from module definition
        valid_ports = set(module.ports.keys())
        mapped_ports = set(instance.mappings.keys()) if instance.mappings else set()
        
        # Check: All mapped ports must exist in module definition
        invalid_ports = mapped_ports - valid_ports
        if invalid_ports:
            diagnostic = create_validator_diagnostic(
                "V0302",
                instance_id=instance_id,
                invalid_ports=sorted(invalid_ports),
                valid_ports=sorted(valid_ports),
                module_name=instance.model,
            )
            diagnostics.append(diagnostic)
        
        return diagnostics
    
    def validate_unused_components(self, asdl_file: ASDLFile) -> List[Diagnostic]:
        """
        Validate and identify unused modules.
        
        Args:
            asdl_file: Complete ASDL design to validate
            
        Returns:
            List of diagnostics (warnings for unused modules)
        """
        diagnostics = []
        
        # Track what modules are used anywhere in the design
        used_modules = set()
        
        # Walk through every module to see what it instantiates
        for module_name, module in asdl_file.modules.items():
            if module.instances:
                for instance in module.instances.values():
                    if instance.model in asdl_file.modules:
                        # This instance references a module defined in this file
                        used_modules.add(instance.model)
        
        # Identify unused modules (exclude top module from unused warnings)
        defined_modules = set(asdl_file.modules.keys())
        unused_modules = defined_modules - used_modules
        
        # Remove top module from unused warnings since it's the entry point
        if asdl_file.file_info.top_module:
            unused_modules.discard(asdl_file.file_info.top_module)
        
        # Generate warning for unused modules  
        if unused_modules:
            modules_list = ", ".join(f"'{module}'" for module in sorted(unused_modules))
            diagnostic = create_validator_diagnostic(
                "V0601",
                modules_list=modules_list,
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
            diagnostic = create_validator_diagnostic(
                "V0401",
                module_name=module_name,
                nets_list=nets_list,
            )
            diagnostics.append(diagnostic)
        
        return diagnostics 
    
    def validate_parameter_overrides(self, instance_id: str, instance: Instance, module: Module) -> List[Diagnostic]:
        """
        Validate parameter override rules for a specific instance.
        
        Rules:
        - Parameter overrides only allowed for primitive modules (spice_template present)
        - Variable overrides never allowed  
        - Hierarchical modules (instances present) cannot have parameter overrides
        - Only existing module parameters can be overridden
        
        Args:
            instance_id: Name of the instance for error reporting
            instance: Instance with parameter overrides to validate
            module: Target module to validate against
            
        Returns:
            List of diagnostics (errors for rule violations)
        """
        diagnostics = []
        
        # No parameter overrides attempted - always valid
        if not instance.parameters:
            return diagnostics
        
        # Check if module is primitive (has spice_template) or hierarchical (has instances)
        is_primitive = bool(module.spice_template)
        is_hierarchical = bool(module.instances)
        
        # Rule 1: Parameter overrides only allowed for primitive modules
        if is_hierarchical:
            override_params = list(instance.parameters.keys())
            diagnostic = create_validator_diagnostic(
                "V0303",
                instance_id=instance_id,
                override_params=override_params,
                module_name=instance.model,
                location=instance,
            )
            diagnostics.append(diagnostic)
            return diagnostics  # Don't check further if it's hierarchical
        
        # Get module's defined parameters and variables for validation
        module_parameters = set(module.parameters.keys()) if module.parameters else set()
        module_variables = set(module.variables.keys()) if module.variables else set()
        
        # Rule 2: Variable overrides never allowed
        attempted_variable_overrides = set(instance.parameters.keys()) & module_variables
        for var_name in sorted(attempted_variable_overrides):
            diagnostic = create_validator_diagnostic(
                "V0304",
                instance_id=instance_id,
                var_name=var_name,
                module_name=instance.model,
                location=instance,
            )
            diagnostics.append(diagnostic)
        
        # Rule 3: Only existing module parameters can be overridden
        attempted_parameter_overrides = set(instance.parameters.keys()) - module_variables  # Exclude variables (already handled)
        non_existent_parameters = attempted_parameter_overrides - module_parameters
        for param_name in sorted(non_existent_parameters):
            if module_parameters:
                available_params = ", ".join(f"'{param}'" for param in sorted(module_parameters))
                details = (f"Instance '{instance_id}' attempts to override non-existent parameter '{param_name}' "
                          f"on module '{instance.model}'. Available parameters: {available_params}.")
            else:
                details = (f"Instance '{instance_id}' attempts to override parameter '{param_name}' "
                          f"on module '{instance.model}', but module defines no parameters.")

            diagnostic = create_validator_diagnostic(
                "V0305",
                details=details,
                location=instance,
            )
            diagnostics.append(diagnostic)
        
        return diagnostics
    
    def validate_file_parameter_overrides(self, asdl_file: ASDLFile) -> List[Diagnostic]:
        """
        Validate parameter override rules across an entire ASDL file.
        
        Args:
            asdl_file: Complete ASDL design to validate
            
        Returns:
            List of diagnostics for all parameter override violations
        """
        all_diagnostics = []
        
        # Check parameter overrides in all modules
        for module_name, module in asdl_file.modules.items():
            if not module.instances:
                continue
                
            for instance_id, instance in module.instances.items():
                # Find the target module for this instance
                target_module = None
                
                # Check if it's a module reference
                if instance.model in asdl_file.modules:
                    target_module = asdl_file.modules[instance.model]
                # Note: For models (device references), parameter overrides are handled differently
                # and are generally allowed since models represent primitive devices
                
                if target_module:
                    instance_diagnostics = self.validate_parameter_overrides(
                        instance_id, instance, target_module
                    )
                    all_diagnostics.extend(instance_diagnostics)
        
        return all_diagnostics
    
    def validate_module_parameter_fields(self, asdl_file: ASDLFile) -> List[Diagnostic]:
        """
        Validate that hierarchical modules don't declare parameters fields.
        
        According to the parameter resolving system:
        - Primitive modules (with spice_template) can declare parameters
        - Hierarchical modules (with instances) should only use variables
        
        Args:
            asdl_file: Complete ASDL design to validate
            
        Returns:
            List of diagnostics for module parameter field violations
        """
        diagnostics = []
        
        for module_name, module in asdl_file.modules.items():
            is_hierarchical = bool(module.instances)
            has_parameters = bool(module.parameters)
            
            # Rule: Hierarchical modules must not declare parameters fields
            if is_hierarchical and has_parameters:
                param_names = list(module.parameters.keys())
                diagnostic = create_validator_diagnostic(
                    "V0201",
                    module_name=module_name,
                    param_names=param_names,
                    location=module,
                )
                diagnostics.append(diagnostic)
        
        return diagnostics